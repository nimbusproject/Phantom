from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, InstanceMonitoringType
from pyhantom.phantom_exceptions import PhantomAWSException

class TestSystem(object):

    def __init__(self):
        self._lcs = {}
        self._asgs = {}

    def create_launch_config(self, lc):
        if lc.LaunchConfigurationName in self._lcs:
            raise PhantomAWSException('AlreadyExists', details=in_lc.LaunchConfigurationName)
        self._lcs[lc.LaunchConfigurationName] = lc

    def get_launch_configs(self, names=None, max=-1, startToken=None):
        if names == None:
            sorted_keys = sorted(self._lcs.keys())
        else:
            for n in names:
                if n not in self._lcs:
                    raise PhantomAWSException('InvalidParameterValue', details=n)
            sorted_keys = sorted(names)

        next_name = None
        if max is None or max < 0:
            max = len(sorted_keys)
        elif max != len(sorted_keys):
            next_name = self._lcs[sorted_keys[max]].LaunchConfigurationName

        activated = False
        if startToken is None:
            activated = True

        lc_list_type = AWSListType()
        for i in range(0, max):
            k = sorted_keys[i]
            if startToken and self._lcs[k] == startToken:
                activated = True
            if not activated:
                continue
            lc_list_type.add_item(self._lcs[k])
            if lc_list_type.get_length() == max:
                return lc_list_type
        return (lc_list_type, next_name)

    def delete_launch_config(self, name):
        if name not in self._lcs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._lcs['name']

    def create_autoscale_group(self, asg):
        if asg.name in self._asgs :
            raise PhantomAWSException('AlreadyExists', details=asg.name)
        self._asgs[asg.name] = asg

    def alter_autoscale_group(self, name, desired_capacity):
        pass

    # add instances to it XXX 
    def get_autoscale_groups(self, names=None, max=-1, start=0):
        if names == None:
            sorted_keys = self._asgs.keys().sort()
        else:
            for n in names:
                if n not in self._asgs:
                    raise PhantomAWSException('InvalidParameterValue', details=n)
            sorted_keys = names.sort()

        if max < 0:
            max = len(sorted_keys)
        asgs = []
        for i in range(start, start+max):
            asgs.append(self._asgs[sorted_keys[i]])
        return asgs

    def delete_autoscale_group(self, name):
        if name not in self._asgs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._asgs['name']

    def get_autoscale_instances(self, instance_id_list=None, max=-1, start=0):
        pass

    def terminate_instances(self, instance_id, adjust_policy):
        pass