from pyhantom.util import not_implemented_decorator

class phdata_store(object):

    @not_implemented_decorator
    def get_user_key(self, access_id):
        return "1234567890"

    @not_implemented_decorator
    def create_launch_config(self, lc):
        pass

    @not_implemented_decorator
    def get_launch_configs(self, name, max=-1, start=0):
        pass

    @not_implemented_decorator
    def delete_launch_config(self, name):
        pass

    @not_implemented_decorator
    def create_autoscale_group(self, name, desired_capacity, launch_config_name, az=None):
        pass

    @not_implemented_decorator
    def alter_autoscale_group(self, name, desired_capacity):
        pass

    @not_implemented_decorator
    def get_autoscale_groups(self, name, max, start):
        pass

    @not_implemented_decorator
    def delete_autoscale_group(self, name):
        pass

    @not_implemented_decorator
    def get_autoscale_instances(self, instance_id_list, max=-1, start=0):
        pass
