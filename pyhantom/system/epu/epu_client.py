import logging
from pyhantom.out_data_types import InstanceType, AWSListType, LaunchConfigurationType, InstanceMonitoringType, DateTimeType
from pyhantom.system import SystemAPI
from pyhantom.system.local_db.persistance import LaunchConfigurationObject
from pyhantom.system.local_db.system import SystemLocalDB
from pyhantom.phantom_exceptions import PhantomAWSException
from ceiclient.connection import DashiCeiConnection
from ceiclient.client import EPUMClient, DTRSDTClient
from pyhantom.util import log, LogEntryDecorator, _get_time, make_time, get_default_keyname
from dashi import DashiError


g_add_template = {'general' :
                    {'engine_class': 'epu.decisionengine.impls.phantom.PhantomEngine'},
                  'health':
                    {'monitor_health': False},
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

def convert_epu_description_to_asg_out(desc, asg):

    inst_list = desc['instances']
    name = desc['name']
    config = desc['config']

    log(logging.DEBUG, "Changing the config: %s" %(str(config)))
    #asg.DesiredCapacity = int(config['engine_conf']['preserve_n'])
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
        out_t.LaunchConfigurationName = asg.LaunchConfigurationName

        if 'iaas_id' in  inst:
            out_t.InstanceId = inst['iaas_id']
        else:
            out_t.InstanceId = ""

        asg.Instances.type_list.append(out_t)

    return asg

class EPUSystem(SystemAPI):

    def __init__(self, cfg):
        ssl = cfg.phantom.system.broker_ssl
        self._broker = cfg.phantom.system.broker
        self._broker_port = cfg.phantom.system.broker_port
        self._rabbitpw = cfg.phantom.system.rabbit_pw
        self._rabbituser = cfg.phantom.system.rabbit_user
        self._rabbitexchange = cfg.phantom.system.rabbit_exchange
        log(logging.INFO, "Connecting to epu messaging fabric: %s, %s, XXXXX, %d, ssl=%s" % (self._broker, self._rabbituser, self._broker_port, str(ssl)))
        self._dashi_conn = DashiCeiConnection(self._broker, self._rabbituser, self._rabbitpw, exchange=self._rabbitexchange, timeout=60, port=self._broker_port, ssl=ssl)
        self._epum_client = EPUMClient(self._dashi_conn)
        self._dtrs_client = DTRSDTClient(self._dashi_conn)

    def _get_dt_details(self, name, caller):
        return self._dtrs_client.describe_dt(caller, name)

    def _check_dt_name_exists(self, name, caller):
        name_list = self._dtrs_client.list_dts(caller)
        return name in name_list


    def _breakup_name(self, name):
        s_a = name.split("@", 1)
        if len(s_a) != 2:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s is not in the proper format.  It must be <dt name>@<site name>" % (name))
        return (s_a)


    @LogEntryDecorator(classname="EPUSystem")
    def create_launch_config(self, user_obj, lc):

        # parse out sitename and dt name from the name
        s_a = lc.LaunchConfigurationName.split("@", 1)
        if len(s_a) != 2:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s is not in the proper format.  It must be <dt name>@<site name>" % (lc.LaunchConfigurationName))

        (dt_name, site_name) = self._breakup_name(lc.LaunchConfigurationName)

        # see if that name already exists
        dt_def = None
        exists = self._check_dt_name_exists(dt_name, user_obj.username)
        if exists:
            dt_def = self._get_dt_details(dt_name, user_obj.username)
        if not dt_def:
            dt_def = {}
            dt_def['mappings'] = {}

        if site_name in dt_def['mappings']:
            raise PhantomAWSException('InvalidParameterValue',details="Name already in use")

        dt_def['mappings'][site_name] = {}
        # values needed by the system
        dt_def['mappings'][site_name]['iaas_allocation'] = lc.InstanceType
        dt_def['mappings'][site_name]['iaas_image'] = lc.ImageId
        dt_def['mappings'][site_name]['key_name'] = get_default_keyname()

        # user defined values
        dt_def['mappings'][site_name]['CreatedTime'] = make_time(lc.CreatedTime.date_time)
        #dt_def['mappings'][site_name]['BlockDeviceMappings'] = lc.BlockDeviceMappings
        dt_def['mappings'][site_name]['InstanceMonitoring'] = lc.InstanceMonitoring.Enabled
        dt_def['mappings'][site_name]['KernelId'] = lc.KernelId
        dt_def['mappings'][site_name]['RamdiskId'] = lc.RamdiskId
        dt_def['mappings'][site_name]['UserData'] = lc.UserData
        dt_def['mappings'][site_name]['RequestedKeyName'] = lc.KeyName
        dt_def['mappings'][site_name]['LaunchConfigurationARN'] = lc.LaunchConfigurationARN

        self._dtrs_client.add_dt(user_obj.username, dt_name, dt_def)


    @LogEntryDecorator(classname="EPUSystem")
    def delete_launch_config(self, user_obj, name):
        (dt_name, site_name) = self._breakup_name(name)
        dt_def = self._get_dt_details(dt_name, user_obj.username)
        if not dt_def:
            raise PhantomAWSException('InvalidParameterValue', details="Name %s not found" % (name))
        if site_name not in dt_def['mappings']:
           raise PhantomAWSException('InvalidParameterValue', details="Name %s not found" % (name))

        del dt_def['mappings'][site_name]

        if len(dt_def['mappings']) == 0:
            self._dtrs_client.remove_dt(user_obj.username, dt_name)
        else:
            self._dtrs_client.update_dt(user_obj.username, dt_name, dt_def)

    @LogEntryDecorator(classname="EPUSystem")
    def get_launch_configs(self, user_obj, names=None, max=-1, startToken=None):
        next_token = None

        dts = self._dtrs_client.list_dts(user_obj.username)
        dts.sort()

        # now that we have the final list, look up each description
        lc_list_type = AWSListType('LaunchConfigurations')
        for lc_name in dts:
            if lc_list_type.get_length() >= max and max > -1:
                break

            dt_descr = self._get_dt_details(lc_name, user_obj.username)
            for site in sorted(dt_descr['mappings'].keys()):
                mapped_def = dt_descr['mappings'][site]
                out_name = '%s@%s' % (lc_name, site)
                if lc_list_type.get_length() >= max and max > -1:
                    break

                if out_name == startToken:
                    startToken = None

                if startToken is None:
                    ot_lc = LaunchConfigurationType('LaunchConfiguration')
                    ot_lc.BlockDeviceMappings = AWSListType('BlockDeviceMappings')

                    tm = _get_time(mapped_def['CreatedTime'])
                    ot_lc.CreatedTime = DateTimeType('CreatedTime', tm)

                    ot_lc.ImageId = mapped_def['iaas_image']
                    ot_lc.InstanceMonitoring = InstanceMonitoringType('InstanceMonitoring')
                    ot_lc.InstanceMonitoring.Enabled = False
                    ot_lc.InstanceType = mapped_def['iaas_allocation']
                    ot_lc.KernelId = None
                    ot_lc.KeyName = get_default_keyname()
                    ot_lc.LaunchConfigurationARN = mapped_def['LaunchConfigurationARN']
                    ot_lc.LaunchConfigurationName = out_name
                    ot_lc.RamdiskId = None
                    ot_lc.SecurityGroups = AWSListType('SecurityGroups')
                    ot_lc.UserData = None

                    lc_list_type.add_item(ot_lc)

        return (lc_list_type, next_token)

    @LogEntryDecorator(classname="EPUSystem")
    def create_autoscale_group(self, user_obj, asg):
        global g_add_template

        if len(asg.AvailabilityZones.type_list) < 1:
            raise PhantomAWSException('InvalidParameterValue', 'An AZ must be specified')
    
        conf = g_add_template.copy()
        conf['engine_conf']['preserve_n'] = asg.DesiredCapacity
        conf['engine_conf']['epuworker_type'] = asg.LaunchConfigurationName
        conf['engine_conf']['force_site'] = asg.AvailabilityZones.type_list[0]

        log(logging.INFO, "Creating autoscale group with %s" % (conf))
        self._epum_client.add_epu(asg.AutoScalingGroupName, conf)

    @LogEntryDecorator(classname="EPUSystem")
    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        self._clean_up_db()
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (asg.AutoScalingGroupName))

        conf = {'engine_conf':
                    {'preserve_n': desired_capacity},
                  }
        self._epum_client.reconfigure_epu(name, conf)

        asg.DesiredCapacity = desired_capacity
        self._db.db_commit()

    @LogEntryDecorator(classname="EPUSystem")
    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        epu_list = self._epum_client.list_epus()
        log(logging.DEBUG, "Incoming epu list is %s" %(str(epu_list)))

        epu_list.sort()
        start_ndx = 0
        if startToken:
            try:
                start_ndx = epu_list.index(startToken)
            except ValueError:
                raise PhantomAWSException('InvalidParameterValue', details="%s was not found in the epu list" % (startToken))

        next_token = None
        end_ndx = len(epu_list)
        if max > -1:
            end_ndx = start_ndx + max
            if end_ndx > len(epu_list):
                end_ndx = len(epu_list)
            if end_ndx < len(epu_list):
                next_token = epu_list[end_ndx]

        epu_list = epu_list[start_ndx:end_ndx]

        for epu in epu_list:
            epu_desc = self._epum_client.describe_epu(epu)

        return (asg_list_type, next_token)


    @LogEntryDecorator(classname="EPUSystem")
    def delete_autoscale_group(self, user_obj, name, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        self._epum_client.remove_epu(name)
