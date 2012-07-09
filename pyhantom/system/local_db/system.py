import logging
from sqlalchemy.exc import IntegrityError
import uuid
from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, DateTimeType, AutoScalingGroupType, InstanceType
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.system import SystemAPI
from pyhantom.system.local_db.persistance import LaunchConfigurationDB, LaunchConfigurationObject, AutoscaleGroupObject


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
    asg.Cooldown = asg_db.DefaultCooldown
    asg.HealthCheckGracePeriod = asg_db.HealthCheckGracePeriod

    asg.AvailabilityZones = AWSListType('AvailabilityZones')
    asg.AvailabilityZones.type_list.append(asg_db.AvailabilityZones)

    asg.CreatedTime = DateTimeType('CreatedTime', asg_db.CreatedTime)

    return asg

class SystemLocalDB(SystemAPI):

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

        # if we ever expect people to have more than a few launch configs we should change this to itertools
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

    def _set_instances(self, asg):
        asg.Instances = AWSListType('Instances')

        for i in range(asg.DesiredCapacity):
            out_t = InstanceType('Instance')

            out_t.AutoScalingGroupName = asg.AutoScalingGroupName
            out_t.HealthStatus = 'Healthy'
            out_t.LifecycleState = '400-Running'
            out_t.AvailabilityZone = 'alamo'
            out_t.LaunchConfigurationName = 'stuff'
            out_t.InstanceId = 'i-' + str(uuid.uuid4()).split('-')[0]
            asg.Instances.type_list.append(out_t)


    def _create_autoscale_group(self, user_obj, asg):
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
        return (db_asg, db_lco[0])

    def create_autoscale_group(self, user_obj, asg):
        (db_asg, db_lc) = self._create_autoscale_group(user_obj, asg)
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
            self._set_instances(a)

        return (asg_list_type, next_token)

    def delete_autoscale_group(self, user_obj, name, force):
        asg = self._db.get_asg(user_obj, name)
        if not asg:
            raise PhantomAWSException('InvalidParameterValue', details="The name %s does not exists" % (name))

        self._db.delete_asg(asg)
        self._db.db_commit()

