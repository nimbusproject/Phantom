from pynimbusauthz.db import DB
from pynimbusauthz.user import User

# The user object for store
class PHDataStore(object):

    def __init__(self, cumulus_db, sql_alch_db):
        self._cumulus_db = cumulus_db

    def get_user_key(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        db = DB(self._cumulus_db)
        user_alias = User.find_alias(access_id, db)
        db.close()
        return user_alias.get_data()
        
    def create_launch_config(self, lc):
        pass

    def get_launch_configs(self, name, max=-1, start=0):
        pass

    def delete_launch_config(self, name):
        pass

    def create_autoscale_group(self, name, desired_capacity, launch_config_name, az=None):
        pass

    def alter_autoscale_group(self, name, desired_capacity):
        pass

    def get_autoscale_groups(self, name, max, start):
        pass

    def delete_autoscale_group(self, name):
        pass

    def get_autoscale_instances(self, instance_id_list, max=-1, start=0):
        pass



def cumulus_get_user_key(access_id):
    DB()
    return "1234567890"
