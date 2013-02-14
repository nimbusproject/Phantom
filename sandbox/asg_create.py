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

if len(sys.argv) < 5:
    sys.exit("usage: %s name lc_name n_preserve cloudname:maxsize ..." % sys.argv[0])

name=sys.argv[1]
lc_name=sys.argv[2]
n_preserve=int(sys.argv[3])

policy_name_key = 'PHANTOM_DEFINITION'
policy_name = 'error_overflow_n_preserving'
ordered_clouds_key = 'clouds'
ordered_clouds = ""
delim = ""
for cloud_size in sys.argv[4:]:
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
