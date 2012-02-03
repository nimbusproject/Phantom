from pyhantom.util import not_implemented_decorator

class PHAuthzIface(object):

    @not_implemented_decorator
    def get_user_key(self, access_id):
        return "1234567890"
