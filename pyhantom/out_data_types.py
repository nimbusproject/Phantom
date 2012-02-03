class AWSListType(object):
    def __init__(self):
        self.type_list = []

    def add_item(self, i):
        self.type_list.append(i)

    def add_xml(self, doc, container_element):
        for l in self.type_list:
            member_el = doc.createElement('member')
            container_element.appendChild(member_el)
            l_el = doc.createElement(l.name)
            member_el.appendChild(l_el)
            l.add_xml(doc, l_el)

    def get_length(self):
        return len(self.type_list)

class AWSType(object):
    members_type_dict = {}
    
    def __init__(self):
        for m in self.members_type_dict:
            if m == AWSListType:
                self.__dict__[m] = AWSListType(m)

    def add_xml(self, doc, container_element):
        for m in self.members_type_dict:
            i_el = doc.createElement(m)
            container_element.appendChild(i_el)
            if m in self.__dict__:
                v = self.__dict__[m]
                t = self.members_type_dict[m]
                if t.isinstance(str) or t.isinstance(int):
                    txt_el = doc.createTextNode(str(v))
                    i_el.appendChild(txt_el)
                else:
                    v.add_xml(doc, i_el)

class EbsType(AWSType):
    members_type_dict = {'SnapshotId': str, 'VolumeSize': int}

    def __init__(self):
        AWSType.__init__(self)

class BlockDeviceMappingType(AWSType):
    members_type_dict = {'DeviceName': str, 'Ebs': EbsType, 'VirtualName': str}

    def __init__(self):
        AWSType.__init__(self)

class DateTimeType(AWSType):
    pass

    def __init__(self):
        AWSType.__init__(self)

class InstanceMonitoringType(AWSType):
    members_type_dict = {'Enabled': bool}

    def __init__(self):
        AWSType.__init__(self)

class LaunchConfigurationType(AWSType):
    members_type_dict = {'BlockDeviceMappings': AWSListType, 'CreatedTime': DateTimeType, 'ImageId' : str,
                         'InstanceMonitoring': InstanceMonitoringType, 'InstanceType': str, 'KernelId': str, 'KeyName': str,
                         'LaunchConfigurationARN': str, 'LaunchConfigurationName': str, 'RamdiskId': str, 'SecurityGroups': AWSListType,
                         'UserData': str}

    def __init__(self):
        AWSType.__init__(self)

        self.InstanceMonitoring = InstanceMonitoringType()
        self.InstanceMonitoring.Enabled = False


    def set_from_intype(self, lc, arn):
        # lct.CreatedTime = XXX?
        self.ImageId = lc.ImageId
        self.InstanceType = lc.InstanceType
        self.KernelId = lc.KernelId
        self.KeyName = lc.KeyName
        self.LaunchConfigurationName = lc.LaunchConfigurationName
        self.LaunchConfigurationARN = arn
        self.RamdiskId = lc.RamdiskId
        self.UserData = lc.UserData
        self.SecurityGroups = AWSListType()
        for sg in lc.SecurityGroups:
            self.SecurityGroups.add_item(sg)


