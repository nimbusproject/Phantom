#!/usr/bin/env python

import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import boto.ec2.autoscale
import urlparse
import sys
import os

username = os.environ['EC2_ACCESS_KEY']
password = os.environ['EC2_SECRET_KEY']
iaas_url = os.environ['PHANTOM_URL']

up = urlparse.urlparse(iaas_url)

ssl = up.scheme == "https"
host = up.hostname
port = up.port

region = RegionInfo(name="nimbus", endpoint=host)
con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=username, aws_secret_access_key=password, is_secure=ssl, port=port, debug=2, region=region, validate_certs=False)
x = con.get_all_groups()

for asg in x:
    print asg.name
    print "\t%s : %d" % (asg.launch_config_name, asg.desired_capacity)
    print "\tInstances:"
    print "\t---------"
    for i in asg.instances:
        print "\t\t%s : %s " % (i.availability_zone, i.health_status)
