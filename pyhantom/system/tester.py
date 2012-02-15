import uuid
from pyhantom.out_data_types import LaunchConfigurationType, AWSListType, InstanceMonitoringType, InstanceType
from pyhantom.phantom_exceptions import PhantomAWSException

g_registry = {}
g_autoscaling_registry = {}
g_instance_registry = {}


def _TESTONLY_clear_registry():
    """This function is here just for testing"""
    global g_registry
    global g_autoscaling_registry
    global g_instance_registry
        
    g_registry = {}
    g_autoscaling_registry = {}
    g_instance_registry = {}

class TestSystem(object):

    def __init__(self):
        global g_registry
        global g_autoscaling_registry
        self._lcs = g_registry
        self._asgs = g_autoscaling_registry

    def create_launch_config(self, user_obj, lc):
        if lc.LaunchConfigurationName in self._lcs:
            raise PhantomAWSException('AlreadyExists', details=lc.LaunchConfigurationName)
        self._lcs[lc.LaunchConfigurationName] = lc

    def get_launch_configs(self, user_obj, names=None, max=-1, startToken=None):
        return self._get_a_list(self._lcs, 'LaunchConfigurations', names, max, startToken)

    def _get_a_list(self, d, list_name, names=None, max=-1, startToken=None):
        if names == None:
            sorted_keys = sorted(d.keys())
        else:
            for n in names:
                if n not in d:
                    empty_list = AWSListType(list_name)
                    return (empty_list, None)
            sorted_keys = sorted(names)

        next_name = None
        if max is None or max < 0:
            max = len(sorted_keys)
        elif max != len(sorted_keys):
            next_name = d[sorted_keys[max]].LaunchConfigurationName

        activated = False
        if startToken is None:
            activated = True

        lc_list_type = AWSListType(list_name)
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

    def delete_launch_config(self, user_obj, name):
        if name not in self._lcs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._lcs[name]

    def create_autoscale_group(self, user_obj, asg):
        if asg.AutoScalingGroupName in self._asgs :
            raise PhantomAWSException('AlreadyExists', details=asg.name)
        self._asgs[asg.AutoScalingGroupName] = asg

    def _make_new_instance(self, asg):
        inst = InstanceType('AutoScalingInstanceDetails')
        inst.AutoScalingGroupName = asg.AutoScalingGroupName
        inst.AvailabilityZone = asg.AvailabilityZones.type_list[0]
        inst.HealthStatus = "Healthy"
        inst.InstanceId = str(uuid.uuid4()).split('-')[0]
        inst.LaunchConfigurationName = asg.LaunchConfigurationName
        inst.LifecycleState = "running"

        asg.Instances.type_list.append(inst)

        g_instance_registry[inst.InstanceId] = inst

    def alter_autoscale_group(self, user_obj, name, desired_capacity, force):
        if name not in self._asgs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        asg = self._asgs[name]
        asg.DesiredCapacity = desired_capacity

        global g_instance_registry
        # add instance up to that capacity
        for i in range(0, desired_capacity):
            self._make_new_instance(asg)

    # add instances to it XXX 
    def get_autoscale_groups(self, user_obj, names=None, max=-1, startToken=None):
        return self._get_a_list(self._asgs, 'AutoScalingGroups', names, max, startToken)

    def delete_autoscale_group(self, user_obj, name, force):
        if name not in self._asgs:
            raise PhantomAWSException('InvalidParameterValue', details=name)
        del self._asgs[name]

    def get_autoscale_instances(self, user_obj, instance_id_list=None, max=-1, startToken=None):
        global g_instance_registry
        return self._get_a_list(g_instance_registry, instance_id_list, max, startToken)

    def terminate_instances(self, user_obj, instance_id, adjust_policy):
        global g_instance_registry
        if instance_id not in g_instance_registry:
            raise PhantomAWSException('InvalidParameterValue', details=instance_id)
        inst = g_instance_registry[instance_id]

        asg = self._asgs[inst.AutoScalingGroupName]
        asg.Instances.type_list.remove(inst)

        if adjust_policy:
            asg.DesiredCapacity = asg.DesiredCapacity - 1
        else:
            self._make_new_instance(asg)
        del g_instance_registry[instance_id]
