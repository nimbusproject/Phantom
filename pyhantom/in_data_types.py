from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import phantom_is_primative


class ObjectFromReqInput(object):

    def __init__(self):
        self.optional_param_list_keys = {}
        self.needed_param_list_keys = {}
        self.optional_param_keys = {}
        self.needed_param_keys = {}

    def _get_value(self, name, in_val, t):
        if t == str:
            val= in_val
        elif t == int:
            val = int(in_val)
        elif t == None:
            # means to skip it (not implemented yet)
            val = None
        elif t == bool:
            if in_val.lower() == 'true':
                val = True
            else:
                val = False
        else:
            o = t()
            val = o.set_from_dict(in_val)
        return val

    def __getattr__(self, item):
        if item in self.optional_param_keys.keys():
            return None
        elif item in self.optional_param_list_keys.keys():
            return None
        raise AttributeError()

    def _do_list_param(self, params, p, type_d):
        for pl in type_d.keys():
            ndx = p.find(pl)
            if ndx == 0:
                if phantom_is_primative(type_d[pl]):
                    val = self._get_value(p, params[p], type_d[pl])
                    if val:
                        if pl not in self.__dict__:
                            self.__dict__[pl] = []
                        self.__dict__[pl].append(val)
                else:
                    if pl not in self.__dict__:
                        self.__dict__[pl] = []
                    l = self.__dict__[pl]
                    member_info = p.split('.', 3)
                    member_ndx = int(member_info[2])
                    for i in range(len(l), int(member_ndx)):
                        l.append(type_d[pl]())

                    element = l[member_ndx-1]
                    value_name = member_info[3]
                    element.set_value(value_name, params[p])

    def set_value(self, name, value):
        if name in self.optional_param_keys:
            t = self.optional_param_keys[name]
        elif name in self.needed_param_keys:
            t = self.needed_param_keys[name]
        elif name in self.optional_param_list_keys:
            raise PhantomAWSException("We cannot work with this type yet")
        elif name in self.needed_param_list_keys:
            raise PhantomAWSException("We cannot work with this type yet")
        else:
            raise PhantomAWSException("%s is not a known value name" % (name))

        if not phantom_is_primative(t):
            raise PhantomAWSException("We cannot work with this type yet")
        self.__setattr__(name, t(value))

    def set_from_dict(self, params):

        for p in self.needed_param_keys.keys():
            if p not in params:
                raise PhantomAWSException('MissingParameter', details="paramter %s missing" % (p))

        for pl in self.needed_param_list_keys.keys():
            found = False
            for p in params:
                ndx = p.find(pl)
                if ndx == 0:
                    found = True
            if not found:
                raise PhantomAWSException('MissingParameter', details="paramter %s missing" % (pl))

        for p in params:
            self._do_list_param(params, p, self.needed_param_list_keys)
            self._do_list_param(params, p, self.optional_param_list_keys)

        # setup the needed ones
        for p in self.needed_param_keys:
            if p in params:
                val = self._get_value(p, params[p], self.needed_param_keys[p])
                if val is not None:
                    self.__dict__[p] = val
        # setup the optional ones
        for p in self.optional_param_keys:
            if p in params:
                val = self._get_value(p, params[p], self.optional_param_keys[p])
                if val is not None:
                    self.__dict__[p] = val

class BlockDeviceMappingInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.optional_param_keys = {"DeviceName": str,  "VirtualName": str}

class TagsInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.needed_param_keys = {"Key": str,  "PropagateAtLaunch": bool, "ResourceId": str, "ResourceType": str, "Value": str}

class LaunchConfigurationInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.optional_param_list_keys = {"BlockDeviceMappings": BlockDeviceMappingInput, "SecurityGroups": str}
        self.optional_param_keys = {"InstanceMonitoring": None,  "KernelId": str, "KeyName": str, "RamdiskId": str,  "UserData": str}
        self.needed_param_keys = {"ImageId": str, "InstanceType": str, "LaunchConfigurationName": str,}

class DeleteLaunchConfigurationInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.needed_param_keys = {"LaunchConfigurationName": str}

class DescribeLaunchConfigurationsInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)
        self.optional_param_keys = {"MaxRecords": int, "NextToken": str}
        self.optional_param_list_keys = {"LaunchConfigurationNames": str}


class CreateAutoScalingGroupInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.needed_param_list_keys = {'AvailabilityZones': str}
        self.optional_param_list_keys = {"Tags": TagsInput, "LoadBalancerNames": str}
        self.optional_param_keys = {"DefaultCooldown": int,  "DesiredCapacity": int, "HealthCheckGracePeriod": int, "HealthCheckType": str,  "PlacementGroup": str, "VPCZoneIdentifier": str}
        self.needed_param_keys = {"AutoScalingGroupName": str, "LaunchConfigurationName": str, "MaxSize": int, "MinSize": int}

class DeleteAutoScalingGroupInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.needed_param_keys = {"AutoScalingGroupName": str}
        self.optional_param_keys = {"ForceDelete": bool}

class DescribeAutoScalingGroupInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.optional_param_keys = {"MaxRecords": int, 'NextToken': str}
        self.optional_param_list_keys = {"AutoScalingGroupNames": str}

class SetDesiredCapacityInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.optional_param_keys = {"HonorCooldown": bool}
        self.needed_param_keys = {"AutoScalingGroupName": str, "DesiredCapacity": int}

class DescribeAutoScalingInstancesInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.optional_param_keys = {"MaxRecords": int, 'NextToken': str}
        self.optional_param_list_keys = {"InstanceIds": str}

class TerminateInstanceInAutoScalingGroupInput(ObjectFromReqInput):
    def __init__(self):
        ObjectFromReqInput.__init__(self)

        self.needed_param_keys = {"InstanceId": str, "ShouldDecrementDesiredCapacity": bool}

