import webob
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.wsgiapps import PhantomBaseService

class DescribeAutoScalingGroups(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(name)

    @webob.dec.wsgify
    def __call__(self, req):
        raise PhantomAWSException('ServiceUnavailable')



