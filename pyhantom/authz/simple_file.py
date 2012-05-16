# The user object for store
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException

class SimpleFileDataStore(PHAuthzIface):

    def __init__(self, filepath):
        self._filepath = filepath

    def get_user_object_by_access_id(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        fptr = open(self._filepath, "r")
        try:
            for line in fptr:
                la = line.split()
                if len(la) != 3:
                    raise PhantomAWSException("InternalFailure", details="Invalid security file %s" % (self._filepath))
                access_key = la[0]
                secret_key = la[1]
                display_name = la[2]
                if access_key == access_id:
                    return PhantomUserObject(access_id, secret_key, display_name)
            raise PhantomAWSException('InvalidClientTokenId')
        finally:
            fptr.close()


