import logging
import webob
import webob.dec
import webob.exc
import uuid
from pyhantom.config import build_cfg
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import authenticate_user, CatchErrorDecorator, LogEntryDecorator, log
from pyhantom.wsgiapps.auto_scaling_group import CreateAutoScalingGroup, DeleteAutoScalingGroup, DescribeAutoScalingGroup, SetDesiredCapacity
from pyhantom.wsgiapps.instances import DescribeAutoScalingInstances, TerminateInstanceInAutoScalingGroup
from pyhantom.wsgiapps.launch_configuration import CreateLaunchConfiguration, DescribeLaunchConfigurations, DeleteLaunchConfiguration
from wsgiref.simple_server import make_server

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

        request_id = str(uuid.uuid4())
        try:
            log(logging.INFO, "%s Enter main router | %s" % (request_id, str(req.params)))
            authz = self._cfg.get_authz()
            user_obj = authz.get_user_object_by_access_id(req.params['AWSAccessKeyId'])
            authenticate_user(req, user_obj.secret_key)
            key = 'Action'
            if key not in req.params.keys():
                raise PhantomAWSException('InvalidParameterValue')
            action = req.params['Action']

            global _action_to_application_map
            if action not in _action_to_application_map:
                raise webob.exc.HTTPNotFound("No action %s" % action)

            app_cls = _action_to_application_map[action]

            log(logging.INFO, "%s Getting phantom action %s" % (request_id, action))
            
            app = app_cls(action)
        except Exception, ex:
            log(logging.ERROR, "%s Exiting main router with error %s" % (request_id, str(ex)))
            raise
        
        log(logging.INFO, "%s Exiting main router" % (request_id))

        return app

if __name__ == '__main__':
    httpd = make_server('127.0.0.1', 8445, MainRouter())
    httpd.serve_forever()