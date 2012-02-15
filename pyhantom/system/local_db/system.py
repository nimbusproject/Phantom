import logging
from sqlalchemy.exc import IntegrityError
from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, DateTimeType, AutoScalingGroupType
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.system import SystemAPI
from pyhantom.system.local_db.persistance import LaunchConfigurationDB, LaunchConfigurationObject, AutoscaleGroupObject

#g_add_template = {'general' :
#                    {'engine_class': 'epu.decisionengine.impls.phantom.PhantomEngine'},
#                  'health':
#                    {'monitor_health': False},
#                  'engine_conf':
#                    {'preserve_n': 1,
#                     'epuworker_type': 'sleeper',
#                     'epuworker_image_id': 'ami-57e52c3e',
#                     'iaas_site': 'ec2-east',
#                     'iaas_allocation': 't1.micro',
#                     'deployable_type': 'sleeper'}
#                  }
#conf = g_add_template.copy()
#conf['engine_conf']['preserve_n'] = asg.DesiredCapacity
#conf['engine_conf']['epuworker_image_id'] = lc.ImageId
#conf['engine_conf']['iaas_site'] = az
#conf['engine_conf']['iaas_allocation'] = lc.InstanceType
        #self._broker = cfg.phantom.system.broker
        #self._rabbitpw = cfg.phantom.system.rabbit_pw
        #self._rabbituser = cfg.phantom.system.rabbit_user
        #self._rabbitexchange = cfg.phantom.system.rabbit_exchange

        #self._dashi_conn = DashiCeiConnection(self._broker, self._rabbituser, self._rabbitpw, exchange=self._rabbitexchange)
        #self._epum_client = EPUMClient(self._dashi_conn)


def db_launch_config_to_outtype(lcdb):
    lc = LaunchConfigurationType('LaunchConfiguration')
    lc.ImageId = lcdb.ImageId
    lc.InstanceType = lcdb.InstanceType
    lc.KernelId = lcdb.KernelId
    lc.KeyName = lcdb.KeyName
    lc.LaunchConfigurationARN = lcdb.LaunchConfigurationARN
    lc.LaunchConfigurationName = lcdb.LaunchConfigurationName
    lc.RamdiskId = lcdb.RamdiskId
    lc.UserData = lcdb.UserData

    for sg in lcdb.security_groups:
        lc.SecurityGroups.type_list.append(sg.name)
    lc.InstanceMonitoring.Enabled = lcdb.InstanceMonitoring
    #lc.BlockDeviceMappings
    lc.CreatedTime = DateTimeType('CreatedTime', lcdb.CreatedTime)

    return lc

def db_asg_to_outtype(asg_db):
    asg = AutoScalingGroupType('AutoScalingGroup')

    asg.AutoScalingGroupName = asg_db.AutoScalingGroupName
    asg.AutoScalingGroupARN = asg_db.AutoScalingGroupARN
    asg.LaunchConfigurationName = asg_db.LaunchConfigurationName
    asg.VPCZoneIdentifier = asg_db.VPCZoneIdentifier
    asg.HealthCheckType = asg_db.HealthCheckType
    asg.PlacementGroup = asg_db.PlacementGroup
    asg.Status = asg_db.Status
    asg.DesiredCapacity = asg_db.DesiredCapacity
    asg.MaxSize = asg_db.MaxSize
    asg.MinSize = asg_db.MinSize
    asg.DefaultCooldown = asg_db.DefaultCooldown
    asg.HealthCheckGracePeriod = asg_db.HealthCheckGracePeriod

    asg.AvailabilityZones = AWSListType('AvailabilityZones')
    asg.AvailabilityZones.type_list.append(asg_db.AvailabilityZones)

    asg.CreatedTime = DateTimeType('CreatedTime', asg_db.CreatedTime)

    return asg

class EPUSystemWithLocalLaunchConfiguration(SystemAPI):

    def __init__(self, cfg, log=logging):
        # cfg.phantom.system.db_url
        self._db = LaunchConfigurationDB(cfg.phantom.system.db_url)
        self._log = log

    def create_launch_config(self, user_obj, lc):
        try:
            lco = LaunchConfigurationObject()
            lco.set_from_outtype(lc, user_obj)
            self._db.db_obj_add(lco)
            self._db.db_commit()
        except IntegrityError, ie:
            self._log.error("DB error %s" % (str(ie)))
            raise PhantomAWSException('InvalidParameterValue',details="Name already in use")

    def get_launch_configs(self, user_obj, names=None, max=-1, startToken=None):
        next_token = None
        use_max = max
        if use_max > -1:
            use_max = max + 1

        db_lco = self._db.get_lcs(user_obj, names, use_max, startToken, log=self._log)

        if max > -1 and db_lco:
            nxt = db_lco.pop(-1)
            next_token = nxt.LaunchConfigurationName

        # if weeverexpect people to have more than a few launch configs we should change this to itertools
        lc_list_type = AWSListType('LaunchConfigurations')
        for lcdb in db_lco:
            lc = db_launch_config_to_outtype(lcdb)
            lc_list_type.type_list.append(lc)

        return (lc_list_type, next_token)


    def delete_launch_config(self, user_obj, name):
        db_lco = self._db.get_lcs(user_obj, [name,], max=1, log=self._log)
        if not db_lco:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        self._db.delete_lc(db_lco[0])
        self._db.db_commit()

    def create_autoscale_group(self, user_obj, asg):
        global g_add_template

        db_asg = self._db.get_asg(user_obj, asg.AutoScalingGroupName)
        if db_asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s already exists" % (asg.AutoScalingGroupName))

        db_lco = self._db.get_lcs(user_obj, [asg.LaunchConfigurationName,], max=1, log=self._log)
        if not db_lco:
            raise PhantomAWSException('InvalidParameterValue', details="The launch configuration name doesn't exist %s" % (asg.LaunchConfigurationName))

        if len(asg.AvailabilityZones.type_list) < 1:
            raise PhantomAWSException('InvalidParameterValue', 'An AZ must be specified')

        db_asg = AutoscaleGroupObject()
        db_asg.set_from_outtype(asg, user_obj)
        self._db.db_obj_add(db_asg)
        self._db.db_commit()


    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (asg.AutoScalingGroupName))

        asg.DesiredCapacity = desired_capacity
        self._db.db_commit()


    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        next_token = None
        use_max = max
        if use_max > -1:
            use_max = max + 1

        db_asgs = self._db.get_asgs(user_obj, names, use_max, startToken, log=self._log)

        if max > -1 and db_asg:
            nxt = db_asg.pop(-1)
            next_token = nxt.AutoScalingGroupName

        asg_list_type = AWSListType('AutoScalingGroups')
        for asgdb in db_asgs:
            a = db_asg_to_outtype(asgdb)
            asg_list_type.type_list.append(a)

        return (asg_list_type, next_token)

    def delete_autoscale_group(self, user_obj, name, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        self._db.delete_asg(asg)
        self._db.db_commit()

