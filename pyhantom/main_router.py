import logging
import urlparse
import webob
import webob.dec
import webob.exc
from wsgiref.simple_server import make_server
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import authenticate_user, CatchErrorDecorator, LogEntryDecorator
from pyhantom.wsgiapps.create_auto_scaling_group import CreateAutoScalingGroup, CreateLaunchConfiguration
from pyhantom.wsgiapps.describe_auto_scaling_group import DescribeAutoScalingGroups

_action_to_application_map = {
    'CreateAutoScalingGroup' : CreateAutoScalingGroup,
    'CreateLaunchConfiguration' : CreateLaunchConfiguration,
    'DeleteAutoScalingGroup' : None,
    'DeleteLaunchConfiguration' : None,
    'DescribeAutoScalingGroups' : DescribeAutoScalingGroups,
    'DescribeAutoScalingInstances' : None,
    'DescribeLaunchConfigurations' : None,
    'SetDesiredCapacity' : None,
    'TerminateInstanceInAutoScalingGroup' : None,
}


class Request(webob.Request):
    pass

class MainRouter(object):

    def __init__(self):
        pass
    
    @webob.dec.wsgify(RequestClass=Request)
    @CatchErrorDecorator(appname="MainRouter")
    @LogEntryDecorator(classname="MainRouter")
    def __call__(self, req):
        key = 'Action'
        if key not in req.params.keys():
            raise PhantomAWSException('InvalidParameterValue')
        action = req.params['Action']

        global _action_to_application_map
        if action not in _action_to_application_map:
            raise webob.exc.HTTPNotFound("No action %s" % action)

        app_cls = _action_to_application_map[action]
        app = app_cls(action)
        authenticate_user(req)
    
        return app

if __name__ == '__main__':
    srv = make_server('localhost', 8080, MainRouter())
    srv.serve_forever()