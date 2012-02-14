from pynimbusauthz.db import DB
from pynimbusauthz.user import User
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException

class CumulusDataStore(PHAuthzIface):

    def __init__(self, cumulus_db):
        self._cumulus_db = cumulus_db

    def get_user_key(self, access_id):
        """Get a new connection every time this is called to make sure it is cleaned up"""
        db = DB(self._cumulus_db)
        user_alias = User.find_alias(access_id, db)
        if not user_alias:
            raise PhantomAWSException('InvalidClientTokenId')
        db.close()
        return PhantomUserObject(access_id, user_alias.get_data())

