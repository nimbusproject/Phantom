import webob
import webob.dec
import webob.exc
from pyhantom.config import build_cfg
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import authenticate_user, CatchErrorDecorator, LogEntryDecorator
from pyhantom.wsgiapps.auto_scaling_group import CreateAutoScalingGroup, DeleteAutoScalingGroup, DescribeAutoScalingGroup, SetDesiredCapacity
from pyhantom.wsgiapps.instances import DescribeAutoScalingInstances, TerminateInstanceInAutoScalingGroup
from pyhantom.wsgiapps.launch_configuration import CreateLaunchConfiguration, DescribeLaunchConfigurations, DeleteLaunchConfiguration

_action_to_application_map = {
    'CreateAutoScalingGroup' : CreateAutoScalingGroup,
    'CreateLaunchConfiguration' : CreateLaunchConfiguration,
    'DeleteAutoScalingGroup' : DeleteAutoScalingGroup,
    'DeleteLaunchConfiguration' : DeleteLaunchConfiguration,
    'DescribeAutoScalingGroups' : DescribeAutoScalingGroup,
    'DescribeAutoScalingInstances' : DescribeAutoScalingInstances,
    'DescribeLaunchConfigurations' : DescribeLaunchConfigurations,
    'SetDesiredCapacity' : SetDesiredCapacity,
    'TerminateInstanceInAutoScalingGroup' : TerminateInstanceInAutoScalingGroup,
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
        user_obj = authz.get_user_key(req.params['AWSAccessKeyId'])
        authenticate_user(req, user_obj.password)
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

