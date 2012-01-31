import uuid
from webob.response import Response
from pyhantom.phantom_exceptions import PhantomAWSException

class PhantomBaseService(object):

    def __init__(self, name):
        self.name = name
        self.ns = "http://autoscaling.amazonaws.com/doc/2010-08-01/"
        self.xamznRequestId = str(uuid.uuid4())

    def get_response(self):
        res = Response()
        res.headers['x-amzn-RequestId'] = self.xamznRequestId
        return res
            

