from pyhantom.phantom_exceptions import PhantomAWSException

class ObjectFromReq(object):

    def __init__(self):
        self.optional_param_list_keys = {}
        self.needed_param_list_keys = {}
        self.optional_param_keys = []
        self.needed_param_keys = []

    def set_from_dict(self, params):

        for p in self.needed_param_keys + self.needed_param_list_keys.keys():
            if p not in params:
                raise PhantomAWSException('MissingParameter', details="paramter %s missing" % (p))

        for p in params:
            for pl in self.needed_param_list_keys.keys():
                ndx = p.find(pl)
                if ndx == 0:
                    self.needed_param_list_keys[pl].append(params[p])
        for p in params:
            for pl in self.optional_param_list_keys.keys():
                ndx = p.find(pl)
                if ndx == 0:
                    self.optional_param_list_keys[pl].append(params[p])

        for p in self.needed_param_list_keys:
            self.__dict__[p] = self.needed_param_list_keys[p]
        for p in self.optional_param_list_keys:
            self.__dict__[p] = self.optional_param_list_keys[p]

        for p in self.needed_param_keys + self.optional_param_keys:
            if p in params:
                self.__dict__[p] = params[p]


class LaunchConfiguration(ObjectFromReq):
    def __init__(self):
        ObjectFromReq.__init__(self)

        self.optional_param_list_keys = {"BlockDeviceMappings": [], "SecurityGroups": []}
        self.optional_param_keys = ["InstanceMonitoring",  "KernelId", "KeyName", "RamdiskId",  "UserData"]
        self.needed_param_keys = ["ImageId", "InstanceType", "LaunchConfigurationName",]




