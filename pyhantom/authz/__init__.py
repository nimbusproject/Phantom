from pyhantom.util import not_implemented_decorator

class PhantomUserObject(object):

    def __init__(self, username, pw):
        self.username = username
        self.password = pw

class PHAuthzIface(object):

    @not_implemented_decorator
    def get_user_object(self, access_id):
        pass

    @not_implemented_decorator
    def add_user(self, access_id, access_secret):
        pass
