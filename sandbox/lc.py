#!/usr/bin/env python

import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import boto.ec2.autoscale
import uuid
import sys


region = RegionInfo('localhost')
con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=username, aws_secret_access_key=password, is_secure=False, port=8445, debug=3, region=region, validate_certs=False)
con.host = 'localhost'
name = "hterX@hotel"
lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=name, image_id="ami-deadbeaf", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')



con.create_launch_configuration(lc)
x = con.get_all_launch_configurations()

print x

#con.delete_launch_configuration(name)
#x = con.get_all_launch_configurations()

print x
