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
con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=username, aws_secret_access_key=password, is_secure=ssl, port=port, debug=2, region=region)
con.host = host

name=sys.argv[1]
lc_name=sys.argv[2]
size=len(sys.argv[3])

lc_a = x = con.get_all_launch_configurations(names=[lc_name,])
if not lc_a:
    print "No such launch configuration"
    sys.exit(1)
lc = lc_a[0]
asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=con, group_name=name, availability_zones=["us-east-1"], min_size=size, max_size=size, launch_config=lc)
con.create_auto_scaling_group(asg)

