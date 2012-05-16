from pyhantom.util import not_implemented_decorator

class PhantomUserObject(object):

    def __init__(self, access_id, secret_key, display_name):
        self.access_id = access_id
        self.secret_key = secret_key
        self.display_name = display_name

class PHAuthzIface(object):

    @not_implemented_decorator
    def get_user_object_by_access_id(self, access_id):
        pass

    @not_implemented_decorator
    def get_user_object_by_display_name(self, display_name):
        pass

    @not_implemented_decorator
    def add_user(self, displayname, access_id, access_secret):
        pass
