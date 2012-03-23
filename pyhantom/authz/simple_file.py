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
                la = line.split()
                if len(la) != 2:
                    raise PhantomAWSException("InternalFailure", details="Invalid security file %s" % (self._filepath))
                user_id = la[0]
                user_pw = la[1]
                if user_id == access_id:
                    return PhantomUserObject(access_id, user_pw)
            raise PhantomAWSException('InvalidClientTokenId')
        finally:
            fptr.close()


