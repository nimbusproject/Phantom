import webob
from pyhantom.in_data_types import DescribeAutoScalingInstancesInput, TerminateInstanceInAutoScalingGroupInput
from pyhantom.util import CatchErrorDecorator
from pyhantom.wsgiapps import PhantomBaseService

class DescribeAutoScalingInstances(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="DescribeAutoScalingInstances")
    def __call__(self, req):
        user_obj = self.get_user_obj(req)

        input = DescribeAutoScalingInstancesInput()
        input.set_from_dict(req.params)

        ids = None
        if input.InstanceIds:
            ids = input.InstanceIds
        (inst_list, next_token) = self._system.get_autoscale_instances(user_obj, instance_id_list=ids, max=input.MaxRecords, startToken=input.NextToken)

        res = self.get_response()
        doc = self.get_default_response_body_dom()

        lc_el = doc.createElement('AutoScalingInstances')
        doc.documentElement.appendChild(lc_el)
        if next_token:
            nt_el = doc.createElement('NextToken')
            doc.documentElement.appendChild(nt_el)
            text_element = doc.createTextNode(next_token)
            nt_el.appendChild(text_element)

        inst_list.add_xml(doc, lc_el)
        res.unicode_body = doc.documentElement.toxml()
        return res

class TerminateInstanceInAutoScalingGroup(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="TerminateInstanceInAutoScalingGroup")
    def __call__(self, req):
        user_obj = self.get_user_obj(req)

        input = TerminateInstanceInAutoScalingGroupInput()
        input.set_from_dict(req.params)

        self._system.terminate_instances(user_obj, input.InstanceId, input.ShouldDecrementDesiredCapacity)

        ############ MUST return an activity type.:w

        res = self.get_response()
        doc = self.get_default_response_body_dom()
        res.unicode_body = doc.documentElement.toprettyxml()
        return res
