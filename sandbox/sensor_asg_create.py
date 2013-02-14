#!/usr/bin/env python

import boto
from boto.regioninfo import RegionInfo
import boto.ec2.autoscale
import urlparse
import sys
import os
from boto.ec2.autoscale import Tag

username = os.environ['EC2_ACCESS_KEY']
password = os.environ['EC2_SECRET_KEY']
iaas_url = os.environ['PHANTOM_URL']

up = urlparse.urlparse(iaas_url)

ssl = up.scheme == "https"
host = up.hostname
port = up.port

region = RegionInfo(name="nimbus", endpoint=host)
con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=username, aws_secret_access_key=password, is_secure=ssl, port=port, debug=0, region=region, validate_certs=False)
con.host = host

name = sys.argv[1]
lc_name = sys.argv[2]
minimum_vms = sys.argv[3]
maximum_vms = sys.argv[4]

policy_name_key = 'PHANTOM_DEFINITION'
policy_name = 'sensor_engine'
sensor_type_key = 'sensor_type'
sensor_type = 'opentsdb'
metric_key = 'metric'
metric = 'load'
sample_function_key =  'sample_function'
sample_function = 'Average'
minimum_vms_key = 'minimum_vms'
maximum_vms_key = 'maximum_vms'
scale_up_threshold_key = 'scale_up_threshold'
scale_up_threshold = 2.0
scale_up_n_vms_key = 'scale_up_n_vms'
scale_up_n_vms = 1
scale_down_threshold_key = 'scale_down_threshold'
scale_down_threshold = 0.5
scale_down_n_vms_key = 'scale_down_n_vms'
scale_down_n_vms = 1
iaas_allocation_key = 'iaas_allocation'
iaas_allocation = 'm1.small'

# make the tags
policy_tag = Tag(connection=con, key=policy_name_key, value=policy_name, resource_id=name)
sensor_type_tag = Tag(connection=con, key=sensor_type_key, value=sensor_type, resource_id=name)
metric_tag = Tag(connection=con, key=metric_key, value=metric, resource_id=name)
sample_function_tag = Tag(connection=con, key=sample_function_key, value=sample_function, resource_id=name)
minimum_vms_tag = Tag(connection=con, key=minimum_vms_key, value=minimum_vms, resource_id=name)
maximum_vms_tag = Tag(connection=con, key=maximum_vms_key, value=maximum_vms, resource_id=name)
scale_up_threshold_tag = Tag(connection=con, key=scale_up_threshold_key, value=scale_up_threshold, resource_id=name)
scale_up_n_vms_tag = Tag(connection=con, key=scale_up_n_vms_key, value=scale_up_n_vms, resource_id=name)
scale_down_threshold_tag = Tag(connection=con, key=scale_down_threshold_key, value=scale_down_threshold, resource_id=name)
scale_down_n_vms_tag = Tag(connection=con, key=scale_down_n_vms_key, value=scale_down_n_vms, resource_id=name)
iaas_allocation_tag = Tag(connection=con, key=iaas_allocation_key, value=iaas_allocation, resource_id=name)

tags = [policy_tag, sensor_type_tag, metric_tag, sample_function_tag,
        minimum_vms_tag, maximum_vms_tag, scale_up_threshold_tag,
        scale_up_n_vms_tag, scale_down_threshold_tag, scale_down_n_vms_tag,
        iaas_allocation_tag]

lc_a = x = con.get_all_launch_configurations(names=[lc_name,])
if not lc_a:
    print "No such launch configuration"
    sys.exit(1)
lc = lc_a[0]
print 'using %s' % (str(lc))
asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=con, group_name=name, availability_zones=["us-east-1"], min_size=minimum_vms, max_size=maximum_vms, launch_config=lc, tags=tags)
con.create_auto_scaling_group(asg)
