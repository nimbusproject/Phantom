import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import boto.ec2.autoscale
import os
import sys

def get_con(port=9999):
    u = os.environ['RABBITMQ_USERNAME']
    p = os.environ['RABBITMQ_PASSWORD']
    region = RegionInfo('localhost')
    con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=u, aws_secret_access_key=p, is_secure=True, port=port, debug=3, region=region)
    con.host = 'localhost'
    return con

def create_group(con, group_name, lcname, ami):
    lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=lcname, image_id=ami, key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='t1.micro')
    con.create_launch_configuration(lc)
    asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=con, group_name=group_name, availability_zones=["us-east"], min_size=1, max_size=5)
    con.create_auto_scaling_group(asg)
    return (asg, lc)


def main(argv=sys.argv):
    con = get_con()

    (a, l) = create_group(con, 'group', 'lc', 'ami-57e52c3e')

    x = con.get_all_launch_configurations()
    print x

    x = con.get_all_groups()
    print x

    con.delete_auto_scaling_group('group')
    con.delete_launch_configuration('lc')
    return 0

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
