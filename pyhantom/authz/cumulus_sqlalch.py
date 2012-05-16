from pynimbusauthz.db import DB
from pynimbusauthz.user import User
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException

class CumulusDataStore(PHAuthzIface):

    def __init__(self, cumulus_db):
        self._cumulus_db = cumulus_db

    def get_user_object_by_access_id(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        db = DB(self._cumulus_db)
        user_alias = User.find_alias(db, access_id)
        if not user_alias:
            raise PhantomAWSException('InvalidClientTokenId')
        l = list(user_alias)
        db.close()
        if l < 1:
            raise PhantomAWSException('InvalidClientTokenId')
        return PhantomUserObject(access_id, l[0].get_data(), l[0].get_friendly_name())


