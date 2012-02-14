import logging
from sqlalchemy.exc import IntegrityError
from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, DateTimeType
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.system import SystemAPI
from pyhantom.system.epu_local_launchconfiguration.persistance import LaunchConfigurationDB, LaunchConfigurationObject


class EPUSystemWithLocalLaunchConfiguration(SystemAPI):

    def __init__(self, cfg, log=logging):
        # cfg.phantom.system.db_url
        self._db = LaunchConfigurationDB(cfg.phantom.system.db_url)
        self._log = log
        pass

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
        db_lco = self._db.get_lcs(user_obj, names, max, startToken, log=self._log)

        next_token = None
        if max > -1 and db_lco:
            max = max + 1
            nxt = db_lco.pop(-1)
            next_token = nxt.LaunchConfigurationName

        # if weeverexpect people to have more than a few launch configs we should change this to itertools
        lc_list_type = AWSListType('LaunchConfigurations')
        for lcdb in db_lco:
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

            lc_list_type.type_list.append(lc)

        return (lc_list_type, next_token)


    def delete_launch_config(self, user_obj, name):
        db_lco = self._db.get_lcs(user_obj, [name,], max=1, log=self._log)
        if not db_lco:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        self._db.delete_lc(db_lco[0])
        self._db.db_commit()

    def create_autoscale_group(self, user_obj, asg):
        pass

    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        pass

    # add instances to it XXX
    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        pass

    def delete_autoscale_group(self, user_obj, name, force):
        pass

    def get_autoscale_instances(self, user_obj, instance_id_list=None, max=-1, startToken=None):
        pass

    def terminate_instances(self, user_obj, instance_id, adjust_policy):
        pass
    