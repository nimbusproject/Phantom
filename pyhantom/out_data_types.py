import datetime
from pyhantom.util import make_time

def _is_primative(t):
    return t == str or t == int or t == bool or t == float or t == unicode

class AWSListType(object):
    def __init__(self, name):
        self.type_list = []
        self.name = name

    def add_item(self, i):
        self.type_list.append(i)

    def add_xml(self, doc, container_element):
        for l in self.type_list:
            member_el = doc.createElement('member')
            container_element.appendChild(member_el)
            if l is None:
                continue
            if _is_primative(type(l)):
                txt_el = doc.createTextNode(str(l))
                member_el.appendChild(txt_el)
            else:
                l_el = doc.createElement(l.name)
                member_el.appendChild(l_el)
                l.add_xml(doc, l_el)

    def get_length(self):
        return len(self.type_list)

class AWSType(object):
    members_type_dict = {}
    
    def __init__(self, name):
        self.name = name
        for m in self.members_type_dict:
            if self.members_type_dict[m] == AWSListType:
                self.__dict__[m] = AWSListType(m)

    def add_xml(self, doc, container_element):
        for m in self.members_type_dict:
            i_el = doc.createElement(m)
            container_element.appendChild(i_el)
            if m in self.__dict__:
                v = self.__dict__[m]
                if v is None:
                    continue
                t = self.members_type_dict[m]
                if _is_primative(t):
                    txt_el = doc.createTextNode(str(v))
                    i_el.appendChild(txt_el)
                else:
                    v.add_xml(doc, i_el)

class EbsType(AWSType):
    members_type_dict = {'SnapshotId': str, 'VolumeSize': int}

    def __init__(self, name):
        AWSType.__init__(self, name)

class BlockDeviceMappingType(AWSType):
    members_type_dict = {'DeviceName': str, 'Ebs': EbsType, 'VirtualName': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

class DateTimeType(AWSType):

    def __init__(self, name, date_time):
        AWSType.__init__(self, name)
        self.date_time = date_time

    def add_xml(self, doc, container_element):
        tm_str = make_time(self.date_time)
        txt_el = doc.createTextNode(tm_str)
        container_element.appendChild(txt_el)

class TagDescription(AWSType):
    members_type_dict = {'Key': str, 'PropagateAtLaunch': bool, 'ResourceId' : str,
                         'ResourceType': str, 'Value': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

class InstanceMonitoringType(AWSType):
    members_type_dict = {'Enabled': bool}

    def __init__(self, name):
        AWSType.__init__(self, name)

class LaunchConfigurationType(AWSType):
    members_type_dict = {'BlockDeviceMappings': AWSListType, 'CreatedTime': DateTimeType, 'ImageId' : str,
                         'InstanceMonitoring': InstanceMonitoringType, 'InstanceType': str, 'KernelId': str, 'KeyName': str,
                         'LaunchConfigurationARN': str, 'LaunchConfigurationName': str, 'RamdiskId': str, 'SecurityGroups': AWSListType,
                         'UserData': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

        self.InstanceMonitoring = InstanceMonitoringType('InstanceMonitoring')
        self.InstanceMonitoring.Enabled = False


    def set_from_intype(self, lc, arn):
        self.CreatedTime = DateTimeType('CreatedTime', datetime.datetime.utcnow())
        self.ImageId = lc.ImageId
        self.InstanceType = lc.InstanceType
        self.KernelId = lc.KernelId
        self.KeyName = lc.KeyName
        self.LaunchConfigurationName = lc.LaunchConfigurationName
        self.LaunchConfigurationARN = arn
        self.RamdiskId = lc.RamdiskId
        self.UserData = lc.UserData
        self.SecurityGroups = AWSListType('SecurityGroups')
        for sg in lc.SecurityGroups:
            self.SecurityGroups.add_item(sg)

class EnabledMetricType(AWSType):
    members_type_dict = {'Granularity': str, 'Metric': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

class InstanceType(AWSType):
    members_type_dict = {'AutoScalingGroupName': str, 'AvailabilityZone': str, 'HealthStatus': str, 'InstanceId' : str,
                         'LaunchConfigurationName': str, 'LifecycleState': str}
    
    def __init__(self, name):
        AWSType.__init__(self, name)

class SuspendedProcessType(AWSType):
    members_type_dict = {'ProcessName': str, 'SuspensionReason': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

class AutoScalingGroupType(AWSType):
    members_type_dict = {'AutoScalingGroupARN': str, 'AutoScalingGroupName': str, 'AvailabilityZones' : AWSListType,
                         'CreatedTime': DateTimeType, 'DefaultCooldown': int, 'DesiredCapacity': int,
                         'EnabledMetrics': AWSListType, 'HealthCheckGracePeriod': int, 'HealthCheckType': str, 'Instances': AWSListType,
                         'LaunchConfigurationName': str, 'LoadBalancerNames': AWSListType, 'MaxSize': int, 'MinSize': int,
                         'PlacementGroup': str, 'Status': AWSListType, 'SuspendedProcesses': AWSListType, 'Tags': AWSListType, 'VPCZoneIdentifier': str}

    def __init__(self, name):
        AWSType.__init__(self, name)

    def set_from_intype(self, asg, arn):
        self.AutoScalingGroupARN = arn
        self.AutoScalingGroupName = asg.AutoScalingGroupName
        self.AvailabilityZones = AWSListType('AvailabilityZones')
        for az in asg.AvailabilityZones:
            self.AvailabilityZones.type_list.append(az)

        self.CreatedTime = DateTimeType('CreatedTime', datetime.datetime.utcnow())
        self.DefaultCooldown = asg.DefaultCooldown
        self.DesiredCapacity = asg.DesiredCapacity

        self.EnabledMetrics = AWSListType('EnabledMetrics')
        self.HealthCheckGracePeriod = asg.HealthCheckGracePeriod
        self.HealthCheckType = asg.HealthCheckType
        self.Instances = AWSListType('Instances')
        self.LaunchConfigurationName = asg.LaunchConfigurationName
        self.LoadBalancerNames = AWSListType('LoadBalancerNames')
        self.MaxSize = asg.MaxSize
        self.MinSize = asg.MinSize
        self.PlacementGroup = asg.PlacementGroup
        self.Status = AWSListType('Status')
        self.SuspendedProcesses = AWSListType('SuspendedProcesses')
        self.Tags = AWSListType('Tags')
        self.VPCZoneIdentifier = asg.VPCZoneIdentifier

        if self.DesiredCapacity is None:
            self.DesiredCapacity = self.MinSize
        # XXX work around for boto
        if self.HealthCheckGracePeriod is None:
            self.HealthCheckGracePeriod = 0
        if self.DefaultCooldown is None:
            self.DefaultCooldown = 0
