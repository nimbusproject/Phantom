import uuid
from webob.response import Response
from pyhantom.config import build_cfg
import xml.dom.minidom
from pyhantom.util import get_aws_access_key

class PhantomBaseService(object):

    def __init__(self, name, cfg=None, authz=None):
        if cfg is None:
            self._cfg = build_cfg()
        else:
            self._cfg = cfg
        self._system = self._cfg.get_system()
        self.name = name
        self.ns = u"http://autoscaling.amazonaws.com/doc/2009-05-15/"
        self.xamznRequestId = str(uuid.uuid4())
        self._authz = self._cfg.get_authz()

    def get_user_obj(self, req):
        access_dict = get_aws_access_key(req)

        user_obj = self._authz.get_user_object_by_access_id(access_dict['AWSAccessKeyId'])
        return user_obj

    def get_default_response_body_dom(self, doc_name=None):
        if doc_name is None:
            doc_name = self.name

        doc = xml.dom.minidom.Document()
        el = doc.createElementNS(self.ns, unicode(doc_name))
        el.setAttribute("xmlns", self.ns)
        doc.appendChild(el)

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
