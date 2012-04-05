import logging
from pyhantom.out_data_types import InstanceType, AWSListType
from pyhantom.system.local_db.system import SystemLocalDB
from pyhantom.phantom_exceptions import PhantomAWSException
from ceiclient.connection import DashiCeiConnection
from ceiclient.client import EPUMClient
from pyhantom.util import log, LogEntryDecorator

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

        if out_t.HealthStatus == "Healthy":
            out_t.InstanceId = inst['iaas_id']
        else:
            out_t.InstanceId = ""

        asg.Instances.type_list.append(out_t)
        
    return asg

class EPUSystemWithLocalDB(SystemLocalDB):

    def __init__(self, cfg):
        SystemLocalDB.__init__(self, cfg)

        ssl = cfg.phantom.system.broker_ssl
        self._broker = cfg.phantom.system.broker
        self._broker_port = cfg.phantom.system.broker_port
        self._rabbitpw = cfg.phantom.system.rabbit_pw
        self._rabbituser = cfg.phantom.system.rabbit_user
        self._rabbitexchange = cfg.phantom.system.rabbit_exchange
        log(logging.INFO, "Connecting to epu messaging fabric: %s, %s, XXXXX, %d, ssl=%s" % (self._broker, self._rabbituser, self._broker_port, str(ssl)))
        self._dashi_conn = DashiCeiConnection(self._broker, self._rabbituser, self._rabbitpw, exchange=self._rabbitexchange, timeout=60, port=self._broker_port, ssl=ssl)
        self._epum_client = EPUMClient(self._dashi_conn)


    @LogEntryDecorator(classname="EPUSystemWithLocalDB")
    def create_autoscale_group(self, user_obj, asg):
        self._clean_up_db()
        # call the parent class
        (db_asg, db_lc) = self._create_autoscale_group(user_obj, asg)

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

        # add to the db if everything else works out
        self._db.db_obj_add(db_asg)
        self._db.db_commit()


    @LogEntryDecorator(classname="EPUSystemWithLocalDB")
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

    @LogEntryDecorator(classname="EPUSystemWithLocalDB")
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


    @LogEntryDecorator(classname="EPUSystemWithLocalDB")
    def delete_autoscale_group(self, user_obj, name, force):
        self._clean_up_db()
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        try:
#            clean up instances
#            epu_desc = self._epum_client.describe_epu(name)
#            inst_list = epu_desc['instances']
#            for inst in inst_list:
#                if 'iaas_id' in inst['iaas_id']:
#                    instance_id = inst['iaas_id']
#
                    
            self._epum_client.remove_epu(name)
        except Exception, ex:
            raise

        self._db.delete_asg(asg)
        self._db.db_commit()

    @LogEntryDecorator(classname="EPUSystemWithLocalDB")
    def _clean_up_db(self):
        try:
            epu_list = self._epum_client.list_epus()
            asgs = self._db.get_asgs(None)

            for asg in asgs:
                if asg.AutoScalingGroupName not in epu_list:
                    log(logging.ERROR, "Cleaning up an ASG that is in the database and not in the epu list: %s" % (asg.AutoScalingGroupName))
                    self._db.delete_asg(asg)
                    self._db.db_commit()
                    log(logging.INFO, "Object %s has been deleted" % (str(asg)))

        except Exception, ex:
            log(logging.ERROR, "An error occurred while attempting to clean up the DB : %s" % (str(ex)))
