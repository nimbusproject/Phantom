import webob
from pyhantom.wsgiapps import PhantomBaseService

class CreateAutoScalingGroup(PhantomBaseService):

    def __init__(self):
        PhantomBaseService.__init__(self)

    @webob.dec.wsgify
    def __call__(self, req):
        pass
