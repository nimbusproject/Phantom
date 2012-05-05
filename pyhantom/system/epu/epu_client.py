import logging
from pyhantom.out_data_types import InstanceType, AWSListType
from pyhantom.system import SystemAPI
from pyhantom.system.local_db.persistance import LaunchConfigurationObject
from pyhantom.system.local_db.system import SystemLocalDB
from pyhantom.phantom_exceptions import PhantomAWSException
from ceiclient.connection import DashiCeiConnection
from ceiclient.client import EPUMClient, DTRSDTClient
from pyhantom.util import log, LogEntryDecorator
from dashi import DashiError

g_add_template = {'general' :
                    {'engine_class': 'epu.decisionengine.impls.phantom.PhantomEngine'},
                  'health':
                    {'monitor_health': False},
                  'engine_conf':
                    {'preserve_n': None,
                     'epuworker_type': 'phantom',
                     'epuworker_image_id': None,
                     'epuworker_allocation': None,
                     'iaas_key': None,
                     'iaas_secret': None,
                     'iaas_site': None,
                     'iaas_allocation': None,
                     'deployable_type': 'phantom'}
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
        dt_def['mappings'][site_name]['allocation'] = lc.InstanceType
        dt_def['mappings'][site_name]['image'] = lc.ImageId

        # user defined values
        dt_def['mappings'][site_name]['CreatedTime'] = str(lc.CreatedTime.date_time)
        #dt_def['mappings'][site_name]['BlockDeviceMappings'] = lc.BlockDeviceMappings
        dt_def['mappings'][site_name]['InstanceMonitoring'] = lc.InstanceMonitoring.Enabled
        dt_def['mappings'][site_name]['KernelId'] = lc.KernelId
        dt_def['mappings'][site_name]['RamdiskId'] = lc.RamdiskId
        dt_def['mappings'][site_name]['UserData'] = lc.UserData
        dt_def['mappings'][site_name]['KeyName'] = lc.KeyName
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

        start_ndx = 0
        if startToken:
            start_ndx = dts.index(startToken)
        if max > -1:
            end_ndx = start_ndx + max
            if len(dts) > end_ndx:
                next_token = dts[end_ndx]
        else:
            end_ndx = len(dts)

        dts = dts[start_ndx:end_ndx]

        # now that we have the final list, look up each description
        lc_list_type = AWSListType('LaunchConfigurations')
        for lc_name in dts:
            dt_descr = self._dtrs_client.describe_dt(user_obj.username, lc_name)
            for site in dt_descr['mappings']:
                out_name = '%s@%s' % (lc_name, site)
            pass
            # convert to xml out type
        
        return (lc_list_type, next_token)

    @LogEntryDecorator(classname="EPUSystem")
    def create_autoscale_group(self, user_obj, asg):
        global g_add_template
        conf = g_add_template.copy()
        conf['engine_conf']['preserve_n'] = asg.DesiredCapacity
        conf['engine_conf']['epuworker_image_id'] = db_lc.ImageId
        conf['engine_conf']['epuworker_allocation'] = db_lc.InstanceType
        conf['engine_conf']['iaas_key'] = user_obj.username
        conf['engine_conf']['iaas_secret'] = user_obj.password
        conf['engine_conf']['iaas_site'] = db_asg.AvailabilityZones + "-" + user_obj.username
        conf['engine_conf']['iaas_allocation'] = db_lc.InstanceType

        log(logging.INFO, "Creating autoscale group with %s" % (conf))
        try:
            self._epum_client.add_epu(asg.AutoScalingGroupName, conf)
        except Exception, ex:
            raise


    @LogEntryDecorator(classname="EPUSystem")
    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        self._clean_up_db()
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (asg.AutoScalingGroupName))

        conf = {'engine_conf':
                    {'preserve_n': desired_capacity},
                  }
        try:
            self._epum_client.reconfigure_epu(name, conf)
        except Exception, ex:
            raise

        asg.DesiredCapacity = desired_capacity
        self._db.db_commit()

    @LogEntryDecorator(classname="EPUSystem")
    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        self._clean_up_db()
        try:
            (asg_list_type, next_token) = SystemLocalDB.get_autoscale_groups(self, user_obj, names, max, startToken)
            epu_list = self._epum_client.list_epus()
            log(logging.DEBUG, "Incoming epu list is %s" %(str(epu_list)))

            # verify that the names are in thelist
            my_list = []
            for grp in asg_list_type.type_list:
                if grp.AutoScalingGroupName not in epu_list:
                    # perhaps all we should do here is log the error and remove the item from the DB
                    # for now make it very obvious that this happened
                    raise PhantomAWSException('InternalFailure', "%s is in the DB but the epu does not know about it" % (grp.AutoScalingGroupName))

                epu_desc = self._epum_client.describe_epu(grp.AutoScalingGroupName)
                convert_epu_description_to_asg_out(epu_desc, grp)
        except Exception, ex:
            raise
        except:
            raise

        return (asg_list_type, next_token)


    @LogEntryDecorator(classname="EPUSystem")
    def delete_autoscale_group(self, user_obj, name, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        try:
            self._epum_client.remove_epu(name)
        except Exception, ex:
            raise

        self._db.delete_asg(asg)
        self._db.db_commit()

    @LogEntryDecorator(classname="EPUSystem")
    def get_autoscale_instances(self, user_obj, instance_id_list=None, max=-1, start=0):
        pass

    @LogEntryDecorator(classname="EPUSystem")
    def terminate_instances(self, user_obj, instance_id, adjust_policy):
        pass