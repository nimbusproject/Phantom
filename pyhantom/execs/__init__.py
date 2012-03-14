import boto
from boto.regioninfo import RegionInfo
import os
import urlparse

def check_env():
    es = ['EC2_ACCESS_KEY', 'EC2_SECRET_KEY', 'PHANTOM_URL']

    for e in es:
        if e not in os.environ:
            raise Exception('The environment variable %s must be set' % (e))

def get_phantom_con():
    u = os.environ['EC2_ACCESS_KEY']
    p = os.environ['EC2_SECRET_KEY']
    url = os.environ['PHANTOM_URL']
    uparts = urlparse.urlparse(url)
    is_secure = uparts.scheme == 'https'
    region = RegionInfo(uparts.hostname)
    con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=u, aws_secret_access_key=p, is_secure=is_secure, port=uparts.port, region=region)
    con.host = uparts.hostname
    return con
