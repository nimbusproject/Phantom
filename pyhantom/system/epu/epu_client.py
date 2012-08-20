import logging
from pyhantom.out_data_types import InstanceType, AWSListType, LaunchConfigurationType, InstanceMonitoringType, DateTimeType, AutoScalingGroupType
from pyhantom.system import SystemAPI
from pyhantom.phantom_exceptions import PhantomAWSException
from ceiclient.connection import DashiCeiConnection
from ceiclient.client import EPUMClient, DTRSDTClient, EPUMDefinitionClient
from pyhantom.util import log, LogEntryDecorator, _get_time, make_time
from dashi import DashiError
from phantomsql import phantom_get_default_key_name


g_definition_name = "phantom0.1def"

g_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomEngine',
    },
    'health' : {
        'monitor_health' : False
    }
}


g_add_template = {
                  'engine_conf':
                    {'preserve_n': None,
                     'epuworker_type': None,
                     'force_site': None}
                  }

def _is_healthy(state):

    a = state.split('-')
    try:
        code = int(a[0])
        if code > 600:
            return "Unhealthy"
        else:
            return "Healthy"
    except:
        log(logging.WARN, "A weird state was found %s" % (state))
        return "Unhealthy"

def _get_key_or_none(config, k):
    if k not in config:
        return None
    return config[k]

def convert_epu_description_to_asg_out(desc, name):

    log(logging.DEBUG, "conversion description: %s" %(str(desc)))

    config = desc['config']['engine_conf']
    
    asg = AutoScalingGroupType('AutoScalingGroup')
    asg.AutoScalingGroupName = desc['name']
    asg.DesiredCapacity = config['preserve_n']
    tm = _get_key_or_none(config, 'CreatedTime')
    if tm:
        tm = _get_time(config['CreatedTime'])
        asg.CreatedTime = DateTimeType('CreatedTime', tm)

    asg.AutoScalingGroupARN = _get_key_or_none(config, 'AutoScalingGroupARN')
    asg.AvailabilityZones = AWSListType('AvailabilityZones')
    asg.AvailabilityZones.add_item(config['force_site'])
    asg.HealthCheckType = _get_key_or_none(config, 'HealthCheckType')
    asg.LaunchConfigurationName = "%s@%s" % (config['epuworker_type'], config['force_site'])
    asg.MaxSize = config['preserve_n']
    asg.MinSize = config['preserve_n']
    asg.PlacementGroup = _get_key_or_none(config,'PlacementGroup')
    #asg.Status
    asg.VPCZoneIdentifier = _get_key_or_none(config,'VPCZoneIdentifier')
    asg.EnabledMetrics = AWSListType('EnabledMetrics')
    asg.HealthCheckGracePeriod = 0
    asg.LoadBalancerNames = AWSListType('LoadBalancerNames')
    asg.SuspendedProcesses = AWSListType('SuspendedProcesses')
    asg.Tags = AWSListType('Tags')
    asg.Cooldown = 0

    inst_list = desc['instances']

    asg.Instances = AWSListType('Instances')

    for inst in inst_list:
        log(logging.DEBUG, "Converting instance %s" %(str(inst)))
        out_t = InstanceType('Instance')

        out_t.AutoScalingGroupName = name
        out_t.HealthStatus = _is_healthy(inst['state'])
        if 'state_desc' in inst and inst['state_desc'] is not None:
            out_t.HealthStatus = out_t.HealthStatus + " " + str(inst['state_desc'])
        out_t.LifecycleState = inst['state']
        out_t.AvailabilityZone = inst['site']
        out_t.LaunchConfigurationName = inst['deployable_type']

        if 'iaas_id' in  inst:
            out_t.InstanceId = inst['iaas_id']
        else:
            out_t.InstanceId = ""

        asg.Instances.type_list.append(out_t)

    return asg


class EPUSystem(SystemAPI):

    def __init__(self, cfg):
        ssl = cfg.phantom.system.rabbit_ssl
        self._rabbit = cfg.phantom.system.rabbit
        self._rabbit_port = cfg.phantom.system.rabbit_port
        self._rabbitpw = cfg.phantom.system.rabbit_pw
        self._rabbituser = cfg.phantom.system.rabbit_user
        self._rabbitexchange = cfg.phantom.system.rabbit_exchange
        log(logging.INFO, "Connecting to epu messaging fabric: %s, %s, XXXXX, %d, ssl=%s" % (self._rabbit, self._rabbituser, self._rabbit_port, str(ssl)))
        self._dashi_conn = DashiCeiConnection(self._rabbit, self._rabbituser, self._rabbitpw, exchange=self._rabbitexchange, timeout=60, port=self._rabbit_port, ssl=ssl)
        self._epum_client = EPUMClient(self._dashi_conn)
        self._dtrs_client = DTRSDTClient(self._dashi_conn)
        self._epum_def_client = EPUMDefinitionClient(self._dashi_conn)

        domain_def_list = self._epum_def_client.list_domain_definitions()
        if g_definition_name not in domain_def_list:
            self._epum_def_client.add_domain_definition(g_definition_name, g_definition)

    def _get_dt_details(self, name, caller):
        return self._dtrs_client.describe_dt(caller, name)

    def _check_dt_name_exists(self, name, caller):
        name_list = self._dtrs_client.list_dts(caller=caller)
        return name in name_list

    def _breakup_name(self, name):
        s_a = name.split("@", 1)
        if len(s_a) != 2:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s is not in the proper format.  It must be <dt name>@<site name>" % (name))
        return (s_a)


    @LogEntryDecorator(classname="EPUSystem")
    def create_launch_config(self, user_obj, lc):
        (dt_name, site_name) = self._breakup_name(lc.LaunchConfigurationName)

        # see if that name already exists
        dt_def = None
        exists = self._check_dt_name_exists(dt_name, user_obj.access_id)
        if exists:
            dt_def = self._get_dt_details(dt_name, user_obj.access_id)
        if not dt_def:
            dt_def = {}
            dt_def['mappings'] = {}

        if site_name in dt_def['mappings']:
            raise PhantomAWSException('InvalidParameterValue',details="Name already in use")

        dt_def['mappings'][site_name] = {}
        # values needed by the system
        dt_def['mappings'][site_name]['iaas_allocation'] = lc.InstanceType
        dt_def['mappings'][site_name]['iaas_image'] = lc.ImageId
        dt_def['mappings'][site_name]['key_name'] = phantom_get_default_key_name()

        # user defined values
        dt_def['mappings'][site_name]['CreatedTime'] = make_time(lc.CreatedTime.date_time)
        #dt_def['mappings'][site_name]['BlockDeviceMappings'] = lc.BlockDeviceMappings
        dt_def['mappings'][site_name]['InstanceMonitoring'] = lc.InstanceMonitoring.Enabled
        dt_def['mappings'][site_name]['KernelId'] = lc.KernelId
        dt_def['mappings'][site_name]['RamdiskId'] = lc.RamdiskId
        dt_def['mappings'][site_name]['UserData'] = lc.UserData
        dt_def['mappings'][site_name]['RequestedKeyName'] = lc.KeyName
        dt_def['mappings'][site_name]['LaunchConfigurationARN'] = lc.LaunchConfigurationARN

        if exists:
            self._dtrs_client.update_dt(user_obj.access_id, dt_name, dt_def)
        else:
            self._dtrs_client.add_dt(user_obj.access_id, dt_name, dt_def)


    @LogEntryDecorator(classname="EPUSystem")
    def delete_launch_config(self, user_obj, name):
        (dt_name, site_name) = self._breakup_name(name)
        dt_def = self._get_dt_details(dt_name, user_obj.access_id)
        if not dt_def:
            raise PhantomAWSException('InvalidParameterValue', details="Name %s not found" % (name))
        if site_name not in dt_def['mappings']:
           raise PhantomAWSException('InvalidParameterValue', details="Name %s not found" % (name))

        del dt_def['mappings'][site_name]

        if len(dt_def['mappings']) == 0:
            self._dtrs_client.remove_dt(user_obj.access_id, dt_name)
        else:
            self._dtrs_client.update_dt(user_obj.access_id, dt_name, dt_def)

    @LogEntryDecorator(classname="EPUSystem")
    def get_launch_configs(self, user_obj, names=None, max=-1, startToken=None):
        next_token = None

        dts = self._dtrs_client.list_dts(user_obj.access_id)
        dts.sort()

        # now that we have the final list, look up each description
        lc_list_type = AWSListType('LaunchConfigurations')
        for lc_name in dts:
            if lc_list_type.get_length() >= max and max > -1:
                break

            dt_descr = self._get_dt_details(lc_name, user_obj.access_id)
            for site in sorted(dt_descr['mappings'].keys()):
                mapped_def = dt_descr['mappings'][site]
                out_name = '%s@%s' % (lc_name, site)
                if lc_list_type.get_length() >= max and max > -1:
                    break

                if out_name == startToken:
                    startToken = None

                if startToken is None and (names is None or out_name in names):
                    ot_lc = LaunchConfigurationType('LaunchConfiguration')
                    ot_lc.BlockDeviceMappings = AWSListType('BlockDeviceMappings')

                    tm = _get_time(mapped_def['CreatedTime'])
                    ot_lc.CreatedTime = DateTimeType('CreatedTime', tm)

                    ot_lc.ImageId = mapped_def['iaas_image']
                    ot_lc.InstanceMonitoring = InstanceMonitoringType('InstanceMonitoring')
                    ot_lc.InstanceMonitoring.Enabled = False
                    ot_lc.InstanceType = mapped_def['iaas_allocation']
                    ot_lc.KernelId = None
                    ot_lc.KeyName = phantom_get_default_key_name()
                    ot_lc.LaunchConfigurationARN = mapped_def['LaunchConfigurationARN']
                    ot_lc.LaunchConfigurationName = out_name
                    ot_lc.RamdiskId = None
                    ot_lc.SecurityGroups = AWSListType('SecurityGroups')
                    ot_lc.UserData = None

                    lc_list_type.add_item(ot_lc)

        # XXX need to set next_token
        return (lc_list_type, next_token)

    @LogEntryDecorator(classname="EPUSystem")
    def create_autoscale_group(self, user_obj, asg):
        global g_add_template

        log(logging.DEBUG, "entering create_autoscale_group with %s" % (asg.LaunchConfigurationName))
        (dt_name, site_name) = self._breakup_name(asg.LaunchConfigurationName)

        conf = g_add_template.copy()
        conf['engine_conf']['preserve_n'] = asg.DesiredCapacity
        conf['engine_conf']['epuworker_type'] = dt_name
        conf['engine_conf']['force_site'] = site_name
        conf['engine_conf']['CreatedTime'] =  make_time(asg.CreatedTime.date_time)
        conf['engine_conf']['AutoScalingGroupARN'] =  asg.AutoScalingGroupARN
        conf['engine_conf']['VPCZoneIdentifier'] =  asg.VPCZoneIdentifier
        conf['engine_conf']['HealthCheckType'] =  asg.HealthCheckType
        conf['engine_conf']['PlacementGroup'] =  asg.PlacementGroup

        log(logging.INFO, "Creating autoscale group with %s" % (conf))
        try:
            self._epum_client.add_domain(asg.AutoScalingGroupName, g_definition_name, conf, caller=user_obj.access_id)
        except DashiError, de:
            if de.exc_type == u'WriteConflictError':
                raise PhantomAWSException('InvalidParameterValue', details="auto scale name already exists")
            log(logging.ERROR, "An error creating ASG: %s" % (str(de)))
            raise

    @LogEntryDecorator(classname="EPUSystem")
    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        conf = {'engine_conf':
                    {'preserve_n': desired_capacity},
                  }
        try:
            self._epum_client.reconfigure_domain(name, conf, caller=user_obj.access_id)
        except DashiError, de:
            log(logging.ERROR, "An error altering ASG: %s" % (str(de)))
            raise

    @LogEntryDecorator(classname="EPUSystem")
    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        epu_list = self._epum_client.list_domains(caller=user_obj.access_id)
        log(logging.DEBUG, "Incoming epu list is %s" %(str(epu_list)))

        next_token = None
        epu_list.sort()

        asg_list_type = AWSListType('AutoScalingGroups')
        for asg_name in epu_list:
            if asg_list_type.get_length() >= max and max > -1:
                break

            if asg_name == startToken:
                startToken = None

            if startToken is None and (names is None or asg_name in names):
                asg_description = self._epum_client.describe_domain(asg_name, caller=user_obj.access_id)
                asg = convert_epu_description_to_asg_out(asg_description, asg_name)
                asg_list_type.add_item(asg)

        # XXX need to set next_token
        return (asg_list_type, next_token)

    @LogEntryDecorator(classname="EPUSystem")
    def delete_autoscale_group(self, user_obj, name, force):
        try:
            log(logging.INFO, "deleting %s for user %s" % (str(name), user_obj.access_id))
            self._epum_client.remove_domain(name, caller=user_obj.access_id)
        except DashiError, de:
            log(logging.ERROR, "An error altering ASG: %s" % (str(de)))
            raise
