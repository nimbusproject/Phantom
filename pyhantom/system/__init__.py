from pyhantom.util import not_implemented_decorator

class SystemAPI(object):

    @not_implemented_decorator
    def create_launch_config(self, user_obj, lc):
        pass

    @not_implemented_decorator
    def get_launch_configs(self, user_obj, names=None, max=-1, startToken=None):
        pass

    @not_implemented_decorator
    def delete_launch_config(self, user_obj, name):
        pass

    @not_implemented_decorator
    def create_autoscale_group(self, user_obj, asg):
        pass

    @not_implemented_decorator
    def alter_autoscale_group(self, user_obj, name, new_conf):
        pass

    @not_implemented_decorator
    def get_autoscale_groups(self, user_obj, names=None, max=-1, start=0):
        pass

    @not_implemented_decorator
    def delete_autoscale_group(self, user_obj, name):
        pass

    @not_implemented_decorator
    def get_autoscale_instances(self, user_obj, instance_id_list=None, max=-1, start=0):
        pass

    @not_implemented_decorator
    def terminate_instances(self, user_obj, instance_id, adjust_policy):
        pass