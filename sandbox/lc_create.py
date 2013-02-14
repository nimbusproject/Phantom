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
con.host = host

name=sys.argv[1]
image_id=sys.argv[2]
key_name="phantomkey"
it="m1.small"

lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=name, image_id=image_id, key_name=key_name, security_groups=['default'], instance_type=it)

con.create_launch_configuration(lc)
