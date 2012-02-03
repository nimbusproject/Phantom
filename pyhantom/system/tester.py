from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, InstanceMonitoringType
from pyhantom.phantom_exceptions import PhantomAWSException

g_registry = {}
g_autoscaling_registry = {}

def _TESTONLY_clear_registry():
    """This function is here just for testing"""
    global g_registry
    global g_autoscaling_registry
        
    g_registry = {}
    g_autoscaling_registry = {}

class TestSystem(object):

    def __init__(self):
        global g_registry
        global g_autoscaling_registry
        self._lcs = g_registry
        self._asgs = g_autoscaling_registry

    def create_launch_config(self, lc):
        if lc.LaunchConfigurationName in self._lcs:
            raise PhantomAWSException('AlreadyExists', details=lc.LaunchConfigurationName)
        self._lcs[lc.LaunchConfigurationName] = lc

    def get_launch_configs(self, names=None, max=-1, startToken=None):
        return self._get_a_list(self._lcs, names, max, startToken)

    def _get_a_list(self, d, names=None, max=-1, startToken=None):
        if names == None:
            sorted_keys = sorted(d.keys())
        else:
            for n in names:
                if n not in d:
                    raise PhantomAWSException('InvalidParameterValue', details=n)
            sorted_keys = sorted(names)

        next_name = None
        if max is None or max < 0:
            max = len(sorted_keys)
        elif max != len(sorted_keys):
            next_name = d[sorted_keys[max]].LaunchConfigurationName

        activated = False
        if startToken is None:
            activated = True

        lc_list_type = AWSListType('LaunchConfigurations')
        for i in range(0, max):
            k = sorted_keys[i]
            if startToken and d[k] == startToken:
                activated = True
            if not activated:
                continue
            lc_list_type.add_item(d[k])
            if lc_list_type.get_length() == max:
                return (lc_list_type, next_name)
        return (lc_list_type, next_name)

    def delete_launch_config(self, name):
        if name not in self._lcs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._lcs[name]

    def create_autoscale_group(self, asg):
        if asg.AutoScalingGroupName in self._asgs :
            raise PhantomAWSException('AlreadyExists', details=asg.name)
        self._asgs[asg.AutoScalingGroupName] = asg

    def alter_autoscale_group(self, name, desired_capacity, force):
        if name not in self._asgs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        asg = self._asgs[name]
        asg.DesiredCapacity = desired_capacity

    # add instances to it XXX 
    def get_autoscale_groups(self, names=None, max=-1, startToken=None):
        return self._get_a_list(self._asgs, names, max, startToken)

    def delete_autoscale_group(self, name, force):
        if name not in self._asgs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._asgs[name]

    def get_autoscale_instances(self, instance_id_list=None, max=-1, start=0):
        pass

    def terminate_instances(self, instance_id, adjust_policy):
        pass