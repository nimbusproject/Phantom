from pynimbusauthz.db import DB
from pynimbusauthz.user import User

# The user object for store
from pyhantom.authz import PHAuthzIface

class SimpleFileDataStore(PHAuthzIface):

    def __init__(self, filepath):
        self._filepath = filepath

    def get_user_key(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        fptr = open(self._filepath, "r")
        user_id = fptr.readline().strip()
        user_pw = fptr.readline().strip()
        fptr.close()

        if access_id != user_id:
            return ""
        return user_pw

