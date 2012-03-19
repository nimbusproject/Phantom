from pynimbusauthz.db import DB
from pynimbusauthz.user import User

# The user object for store
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException

class SimpleFileDataStore(PHAuthzIface):

    def __init__(self, filepath):
        self._filepath = filepath

    def get_user_key(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        fptr = open(self._filepath, "r")
        try:
            for line in fptr:
                (user_id, user_pw) = line.split()
                if user_id == access_id:
                    return PhantomUserObject(access_id, user_pw)
            raise PhantomAWSException('InvalidClientTokenId')
        finally:
            fptr.close()


