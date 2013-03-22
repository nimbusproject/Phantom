import logging

import webob

from pyhantom.in_data_types import CreateAutoScalingGroupInput, DeleteAutoScalingGroupInput, DescribeAutoScalingGroupInput, SetDesiredCapacityInput, CreateOrUpdateTagsInput
from pyhantom.out_data_types import AutoScalingGroupType
from pyhantom.util import CatchErrorDecorator, make_arn, log, log_reply, log_request, statsd
from pyhantom.wsgiapps import PhantomBaseService
from pyhantom.system.epu.definitions import tags_to_definition

class CreateAutoScalingGroup(PhantomBaseService):

    def __init__(self, name, cfg=None, authz=None):
        PhantomBaseService.__init__(self, name, cfg, authz)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="CreateAutoScalingGroup")
    @statsd
    def __call__(self, req):

        user_obj = self.get_user_obj(req)
        log_request(req, user_obj)

        input = CreateAutoScalingGroupInput()
        input.set_from_dict(req.params)

        arn = make_arn(input.AutoScalingGroupName, self.xamznRequestId, 'autoScalingGroupName')
        asg = AutoScalingGroupType('AutoScalingGroup')
        asg.set_from_intype(input, arn)

        self._system.create_autoscale_group(user_obj, asg)

        res = self.get_response()
        doc = self.get_default_response_body_dom(doc_name="CreateAutoScalingGroupResponse")
        res.unicode_body = doc.documentElement.toprettyxml()
        log_reply(doc, user_obj)
        return res

class DeleteAutoScalingGroup(PhantomBaseService):

    def __init__(self, name, cfg=None, authz=None):
        PhantomBaseService.__init__(self, name, cfg, authz)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="DeleteAutoScalingGroup")
    @statsd
    def __call__(self, req):
        user_obj = self.get_user_obj(req)
        log_request(req, user_obj)

        input = DeleteAutoScalingGroupInput()
        input.set_from_dict(req.params)

        forceit = False
        if input.ForceDelete:
            forceit = True
        self._system.delete_autoscale_group(user_obj, input.AutoScalingGroupName, forceit)
        
        res = self.get_response()
        doc = self.get_default_response_body_dom(doc_name="DeleteAutoScalingGroupResponse")
        res.unicode_body = doc.documentElement.toprettyxml()
        log_reply(doc, user_obj)
        return res

class DescribeAutoScalingGroup(PhantomBaseService):

    def __init__(self, name, cfg=None, authz=None):
        PhantomBaseService.__init__(self, name, cfg, authz)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="DescribeAutoScalingGroup")
    @statsd
    def __call__(self, req):
        user_obj = self.get_user_obj(req)
        log_request(req, user_obj)

        input = DescribeAutoScalingGroupInput()
        input.set_from_dict(req.params)

        names = None
        if input.AutoScalingGroupNames:
            names = input.AutoScalingGroupNames
        (ags_list, next_token) = self._system.get_autoscale_groups(user_obj, names=names, max=input.MaxRecords, startToken=input.NextToken)

        res = self.get_response()
        doc = self.get_default_response_body_dom(doc_name="DescribeAutoScalingGroupsResponse")

        dlcr_el = doc.createElement('DescribeAutoScalingGroupsResult')
        doc.documentElement.appendChild(dlcr_el)

        lc_el = doc.createElement('AutoScalingGroups')
        dlcr_el.appendChild(lc_el)

        if next_token:
            nt_el = doc.createElement('NextToken')
            doc.documentElement.appendChild(nt_el)
            text_element = doc.createTextNode(next_token)
            nt_el.appendChild(text_element)

        ags_list.add_xml(doc, lc_el)
        res.unicode_body = doc.documentElement.toxml()
        log_reply(doc, user_obj)
        return res


class SetDesiredCapacity(PhantomBaseService):

    def __init__(self, name, cfg=None, authz=None):
        PhantomBaseService.__init__(self, name, cfg, authz)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="SetDesiredCapacity")
    @statsd
    def __call__(self, req):
        user_obj = self.get_user_obj(req)
        log_request(req, user_obj)

        input = SetDesiredCapacityInput()
        input.set_from_dict(req.params)

        force = False
        if input.HonorCooldown:
            force = True

        new_conf = {'desired_capacity': input.DesiredCapacity}
        self._system.alter_autoscale_group(user_obj, input.AutoScalingGroupName, new_conf, force)

        res = self.get_response()
        doc = self.get_default_response_body_dom(doc_name="SetDesiredCapacityResponse")
        res.unicode_body = doc.documentElement.toprettyxml()

        log(logging.INFO, "User %s change %s capacity to %d" % (user_obj.access_id, input.AutoScalingGroupName, input.DesiredCapacity))
        log_reply(doc, user_obj)
        return res


class CreateOrUpdateTags(PhantomBaseService):

    def __init__(self, name, cfg=None, authz=None):
        PhantomBaseService.__init__(self, name, cfg, authz)

    @webob.dec.wsgify
    @CatchErrorDecorator(appname="CreateOrUpdateTags")
    @statsd
    def __call__(self, req):

        user_obj = self.get_user_obj(req)
        log_request(req, user_obj)

        input = CreateOrUpdateTagsInput()
        input.set_from_dict(req.params)

        # first we need to organize the tags by group association
        tag_groups = {}
        for tag in input.Tags:
            if tag.ResourceId not in tag_groups:
                tag_groups[tag.ResourceId] = []
            l = tag_groups[tag.ResourceId]
            l.append(tag)

        for group_name in tag_groups:
            log(logging.INFO, "Processing tags for the group %s" % (group_name))

            tags = tag_groups[group_name]
            (name, new_conf) = tags_to_definition(tags)
            
            self._system.alter_autoscale_group(user_obj, group_name, new_conf, force=True)

        res = self.get_response()
        doc = self.get_default_response_body_dom(doc_name="CreateOrUpdateTagsResponse")
        res.unicode_body = doc.documentElement.toprettyxml()

        log_reply(doc, user_obj)
        return res
