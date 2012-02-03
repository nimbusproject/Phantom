import webob
import webob.dec
import webob.exc
from wsgiref.simple_server import make_server
from pyhantom.config import build_cfg
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import authenticate_user, CatchErrorDecorator, LogEntryDecorator
from pyhantom.wsgiapps.auto_scaling_group import CreateAutoScalingGroup
from pyhantom.wsgiapps.launch_configuration import CreateLaunchConfiguration, DescribeLaunchConfigurations, DeleteLaunchConfiguration

_action_to_application_map = {
    'CreateAutoScalingGroup' : CreateAutoScalingGroup,
    'CreateLaunchConfiguration' : CreateLaunchConfiguration,
    'DeleteAutoScalingGroup' : None,
    'DeleteLaunchConfiguration' : DeleteLaunchConfiguration,
    'DescribeAutoScalingGroups' : None,
    'DescribeAutoScalingInstances' : None,
    'DescribeLaunchConfigurations' : DescribeLaunchConfigurations,
    'SetDesiredCapacity' : None,
    'TerminateInstanceInAutoScalingGroup' : None,
}


class Request(webob.Request):
    pass

class MainRouter(object):

    def __init__(self):
        self._cfg = build_cfg()

    @webob.dec.wsgify(RequestClass=Request)
    @CatchErrorDecorator(appname="MainRouter")
    @LogEntryDecorator(classname="MainRouter")
    def __call__(self, req):

        authz = self._cfg.get_authz()
        access_key = authz.get_user_key(req.params['AWSAccessKeyId'])
        authenticate_user(req, access_key)
        key = 'Action'
        if key not in req.params.keys():
            raise PhantomAWSException('InvalidParameterValue')
        action = req.params['Action']

        global _action_to_application_map
        if action not in _action_to_application_map:
            raise webob.exc.HTTPNotFound("No action %s" % action)

        app_cls = _action_to_application_map[action]
        app = app_cls(action)

        return app

if __name__ == '__main__':
    srv = make_server('localhost', 8080, MainRouter())
    srv.serve_forever()