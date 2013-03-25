import logging
import time
import uuid

import webob
import webob.dec
import webob.exc
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import authenticate_user, CatchErrorDecorator, LogEntryDecorator, log, get_aws_access_key
from pyhantom.wsgiapps import PhantomBaseService
from pyhantom.wsgiapps.auto_scaling_group import CreateAutoScalingGroup, DeleteAutoScalingGroup, DescribeAutoScalingGroup, SetDesiredCapacity, CreateOrUpdateTags
from pyhantom.wsgiapps.instances import DescribeAutoScalingInstances, TerminateInstanceInAutoScalingGroup
from pyhantom.wsgiapps.launch_configuration import CreateLaunchConfiguration, DescribeLaunchConfigurations, DeleteLaunchConfiguration
from wsgiref.simple_server import make_server

_action_to_application_map = {
    'CreateAutoScalingGroup' : CreateAutoScalingGroup,
    'CreateOrUpdateTags' : CreateOrUpdateTags,
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


class MainRouter(PhantomBaseService):

    def __init__(self):
        PhantomBaseService.__init__(self, "MainRouter")

    @webob.dec.wsgify(RequestClass=Request)
    @CatchErrorDecorator(appname="MainRouter")
    @LogEntryDecorator(classname="MainRouter")
    def __call__(self, req):
        before = time.time()
        user_obj = None
        request_id = str(uuid.uuid4())
        try:
            log(logging.INFO, "%s Enter main router | %s" % (request_id, str(req.params)))
            authz = self._cfg.get_authz()

            access_dict = get_aws_access_key(req)
            user_obj = authz.get_user_object_by_access_id(access_dict['AWSAccessKeyId'])
            authenticate_user(user_obj.secret_key, req, access_dict)
            key = 'Action'
            if key not in req.params.keys():
                raise PhantomAWSException('InvalidParameterValue')
            action = req.params['Action']

            global _action_to_application_map
            if action not in _action_to_application_map:
                raise webob.exc.HTTPNotFound("No action %s" % action)

            app_cls = _action_to_application_map[action]

            log(logging.INFO, "%s Getting phantom action %s" % (request_id, action))

            app = app_cls(action, cfg=self._cfg)
        except Exception, ex:
            log(logging.ERROR, "%s Exiting main router with error %s" % (request_id, str(ex)))
            raise
        finally:
            #if user_obj:
            #    user_obj.close()
            after = time.time()
            if self._cfg.statsd_client is not None:
                self._cfg.statsd_client.incr('autoscale.MainRouter.count')
                self._cfg.statsd_client.timing('autoscale.MainRouter.timing', (after - before) * 1000)
            pass

        log(logging.INFO, "%s Exiting main router" % (request_id))

        return app

if __name__ == '__main__':
    httpd = make_server('127.0.0.1', 8445, MainRouter())
    httpd.serve_forever()
