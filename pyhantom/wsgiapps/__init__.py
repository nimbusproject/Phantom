import uuid
from webob.response import Response
from pyhantom.config import build_cfg
from pyhantom.phantom_exceptions import PhantomAWSException
from xml.dom.minidom import getDOMImplementation

class PhantomBaseService(object):

    def __init__(self, name):
        self._cfg = build_cfg()
        self._system = self._cfg.get_system()
        self.name = name
        self.ns = "http://autoscaling.amazonaws.com/doc/2010-08-01/"
        self.xamznRequestId = str(uuid.uuid4())

    def get_default_response_body_dom(self):
        impl = getDOMImplementation()
        doc = impl.createDocument(self.ns, self.name, None)
        top_element = doc.documentElement
        resp_el = doc.createElement('ResponseMetadata')
        top_element.appendChild(resp_el)
        reqid_el = doc.createElement('RequestId')
        resp_el.appendChild(reqid_el)
        text_element = doc.createTextNode(self.xamznRequestId)
        reqid_el.appendChild(text_element)
        return doc

    def get_response(self):
        res = Response()
        res.headers['x-amzn-RequestId'] = self.xamznRequestId
        return res


            

