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


