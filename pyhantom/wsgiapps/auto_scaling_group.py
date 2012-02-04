import logging
import webob
from pyhantom.in_data_types import CreateAutoScalingGroupInput, DeleteAutoScalingGroupInput, DescribeAutoScalingGroupInput, SetDesiredCapacityInput
from pyhantom.out_data_types import AutoScalingGroupType
from pyhantom.util import CatchErrorDecorator, make_arn, log
from pyhantom.wsgiapps import PhantomBaseService

class CreateAutoScalingGroup(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="CreateAutoScalingGroup")
    def __call__(self, req):
        input = CreateAutoScalingGroupInput()
        input.set_from_dict(req.params)

        arn = make_arn(input.AutoScalingGroupName, self.xamznRequestId, 'autoScalingGroupName')
        asg = AutoScalingGroupType('AutoScalingGroup')
        asg.set_from_intype(input, arn)

        self._system.create_autoscale_group(asg)

        res = self.get_response()
        doc = self.get_default_response_body_dom()
        res.unicode_body = doc.documentElement.toprettyxml()
        return res

class DeleteAutoScalingGroup(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="DeleteAutoScalingGroup")
    def __call__(self, req):
        input = DeleteAutoScalingGroupInput()
        input.set_from_dict(req.params)

        forceit = False
        if input.ForceDelete:
            forceit = True
        self._system.delete_autoscale_group(input.AutoScalingGroupName, forceit)
        
        res = self.get_response()
        doc = self.get_default_response_body_dom()
        res.unicode_body = doc.documentElement.toprettyxml()
        return res

class DescribeAutoScalingGroup(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="DescribeAutoScalingGroup")
    def __call__(self, req):
        input = DescribeAutoScalingGroupInput()
        input.set_from_dict(req.params)

        names = None
        if input.AutoScalingGroupNames:
            names = input.AutoScalingGroupNames
        (ags_list, next_token) = self._system.get_autoscale_groups(names=names, max=input.MaxRecords, startToken=input.NextToken)

        res = self.get_response()
        doc = self.get_default_response_body_dom()
        
        lc_el = doc.createElement('AutoScalingGroups')
        doc.documentElement.appendChild(lc_el)
        if next_token:
            nt_el = doc.createElement('NextToken')
            doc.documentElement.appendChild(nt_el)
            text_element = doc.createTextNode(next_token)
            nt_el.appendChild(text_element)

        ags_list.add_xml(doc, lc_el)
        res.unicode_body = doc.documentElement.toxml()
        log(logging.INFO, doc.documentElement.toprettyxml())
        return res


class SetDesiredCapacity(PhantomBaseService):

    def __init__(self, name):
        PhantomBaseService.__init__(self, name)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="SetDesiredCapacity")
    def __call__(self, req):
        input = SetDesiredCapacityInput()
        input.set_from_dict(req.params)

        force = False
        if input.HonorCooldown:
            force = True

        self._system.alter_autoscale_group(input.AutoScalingGroupName, input.DesiredCapacity, force)

        res = self.get_response()
        doc = self.get_default_response_body_dom()
        res.unicode_body = doc.documentElement.toprettyxml()
        return res
