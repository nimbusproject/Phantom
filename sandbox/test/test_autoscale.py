#!/usr/bin/env python

import os
import sys
import time
import urlparse
import uuid

from boto.ec2.autoscale import Tag
from boto.regioninfo import RegionInfo
import boto
import boto.ec2.autoscale

username = os.environ['PHANTOM_IAAS_ACCESS_KEY']
password = os.environ['PHANTOM_IAAS_SECRET_KEY']
iaas_url = os.environ['PHANTOM_URL']
cloud = os.environ['PHANTOM_IAAS']

up = urlparse.urlparse(iaas_url)

ssl = up.scheme == "https"
host = up.hostname
port = up.port

region = RegionInfo(name="nimbus", endpoint=host)
con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=username, aws_secret_access_key=password, is_secure=ssl, port=port, debug=2, region=region, validate_certs=False)
con.host = host

lc_name = 'lc-' + uuid.uuid4().hex + '@' + cloud
image_id = os.environ['PHANTOM_IMAGE']
key_name = "phantomkey"
it = "m1.small"
user_data = 'USERDATA_TEST_STRING'

initial = con.get_all_launch_configurations()
try:
    lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=lc_name, image_id=image_id, key_name=key_name, security_groups=['default'], instance_type=it, user_data=user_data)
    con.create_launch_configuration(lc)
    after_create = con.get_all_launch_configurations()

    assert len(after_create) == len(initial) + 1
    assert after_create[0].name == lc_name
    assert after_create[0].image_id == image_id
    assert after_create[0].instance_type == it
    assert after_create[0].key_name == key_name
    assert after_create[0].user_data == user_data

    initial = con.get_all_groups()

    name = 'asg-' + uuid.uuid4().hex
    n_preserve = 1

    policy_name_key = 'PHANTOM_DEFINITION'
    policy_name = 'error_overflow_n_preserving'
    ordered_clouds_key = 'clouds'
    ordered_clouds = ""
    delim = ""
    for cloud_size in ["%s:1" % cloud]:
        (cloudname, maxsize) = cloud_size.split(':')
        ordered_clouds = ordered_clouds + delim + cloud_size
        delim = ","

    n_preserve_key = 'minimum_vms'

    # make the tags
    policy_tag = Tag(connection=con, key=policy_name_key, value=policy_name, resource_id=name)
    clouds_tag = Tag(connection=con, key=ordered_clouds_key, value=ordered_clouds, resource_id=name)
    npreserve_tag = Tag(connection=con, key=n_preserve_key, value=n_preserve, resource_id=name)

    tags = [policy_tag, clouds_tag, npreserve_tag]

    lc_a = x = con.get_all_launch_configurations(names=[lc_name,])
    if not lc_a:
        print "No such launch configuration"
        sys.exit(1)

    lc = lc_a[0]
    print 'using %s' % (str(lc))
    asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=con, group_name=name, availability_zones=["us-east-1"], min_size=n_preserve, max_size=n_preserve, launch_config=lc, tags=tags)
    con.create_auto_scaling_group(asg)

    time.sleep(10)

    after_create = con.get_all_groups()
    assert len(after_create) == len(initial) + 1

    asg_list = filter(lambda a: a.name == name, after_create)
    assert len(asg_list) == 1

    asg = asg_list[0]
    assert len(asg.instances) == n_preserve

    asg.delete()

    time.sleep(30)

    after_delete = con.get_all_groups()
    assert len(after_delete) == len(initial)

finally:
    con.delete_launch_configuration(lc_name)
    after_delete = con.get_all_launch_configurations()
    assert len(after_delete) == len(initial)
