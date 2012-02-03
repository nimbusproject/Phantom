from pyhantom.util import not_implemented_decorator

class SystemAPI(object):

    @not_implemented_decorator
    def create_launch_config(self, lc):
        pass

    @not_implemented_decorator
    def get_launch_configs(self, names=None, max=-1, startToken=None):
        pass

    @not_implemented_decorator
    def delete_launch_config(self, name):
        pass

    @not_implemented_decorator
    def create_autoscale_group(self, asg):
        pass

    @not_implemented_decorator
    def alter_autoscale_group(self, name, desired_capacity):
        pass

    @not_implemented_decorator
    def get_autoscale_groups(self, names=None, max=-1, start=0):
        pass

    @not_implemented_decorator
    def delete_autoscale_group(self, name):
        pass

    @not_implemented_decorator
    def get_autoscale_instances(self, instance_id_list=None, max=-1, start=0):
        pass

    @not_implemented_decorator
    def terminate_instances(self, instance_id, adjust_policy):
        pass