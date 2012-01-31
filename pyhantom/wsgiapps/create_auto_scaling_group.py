import webob
from webob.response import Response
import xml.dom.minidom as xml
from pyhantom.data_types import LaunchConfiguration
from pyhantom.db import create_launch_config
from pyhantom.wsgiapps import PhantomBaseService

class CreateAutoScalingGroup(PhantomBaseService):

    def __init__(self):
        PhantomBaseService.__init__(self)

    @webob.dec.wsgify
    def __call__(self, req):
        lc = LaunchConfiguration()
        lc.set_from_dict(req.params)

class CreateLaunchConfiguration(PhantomBaseService):
    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    def __call__(self, req):
        lc = LaunchConfiguration()

        try:
            lc.set_from_dict(req.params)
            create_launch_config(lc)
        except Exception, ex:
            raise

        res = self.get_response()
        res.unicode_body = self._make_reply()
        return res

    def _make_reply(self):
        body = """
<%s xmlns="%s/">
  <ResponseMetadata>
    <RequestId>%s</RequestId>
  </ResponseMetadata>
</%s>
""" % (self.name, self.ns, self.xamznRequestId, self.name)
        return body

