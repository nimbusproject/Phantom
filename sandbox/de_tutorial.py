import os
import time
import urlparse
import boto
import boto.ec2.autoscale

#from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
from boto.ec2.autoscale import Tag
from boto.ec2.autoscale.launchconfig import LaunchConfiguration
from boto.ec2.autoscale.group import AutoScalingGroup


class MyPhantomDecisionEngine(object):

    def __init__(self):

        self.username = os.environ['EC2_ACCESS_KEY']
        self.password = os.environ['EC2_SECRET_KEY']
        self.iaas_url = os.environ['PHANTOM_URL']

        self.domain_name = "my_domain"
        self.launch_config_name = "my_launch_config"
        self.vm_image = "hello-phantom.gz"
        self.max_vms = 4
        self.key_name = "phantomkey"
        self.image_type = "m1.small"
        self.clouds = ["hotel", "sierra"]

        # Create our Phantom connection
        parsed_url = urlparse.urlparse(self.iaas_url)
        ssl = parsed_url.scheme == "https"
        host = parsed_url.hostname
        port = parsed_url.port

        region = RegionInfo(name="nimbus", endpoint=host)
        self.connection = boto.ec2.autoscale.AutoScaleConnection(
            aws_access_key_id=self.username,
            aws_secret_access_key=self.password,
            is_secure=ssl, port=port, debug=2, region=region,
            validate_certs=False)
        self.connection.host = host

        self.create_launch_configuration()
        self.create_domain()
        self.run_policy()

    def create_launch_configuration(self):

        #create_domain Get a list of existing launch configurations
        existing_launch_configurations = self.connection.get_all_launch_configurations()
        existing_lc_names = [lc.name for lc in existing_launch_configurations]

        # Create launch configurations that don't exist
        for cloud in self.clouds:
            full_lc_name = "%s@%s" % (self.launch_config_name, cloud)

            if not full_lc_name in existing_lc_names:
                print "Creating launch config '%s'" % full_lc_name
                launch_config = LaunchConfiguration(
                    self.connection, name=full_lc_name, image_id=self.image,
                    key_name=self.key_name, security_groups=['default'],
                    instance_type=self.image_type)

                self.connection.create_launch_configuration(launch_config)
            else:
                print "Launch config '%s' has already been added, skipping..." % (full_lc_name,)

    def create_domain(self):

        # Set our policy name
        policy_name_key = 'PHANTOM_DEFINITION'
        policy_name = 'error_overflow_n_preserving'

        # Set the order of clouds in which VMs are started
        ordered_clouds_key = 'clouds'
        ordered_clouds = ""
        cloud_size_pairs = ["%s:%s" % (cloud, self.max_vms) for cloud in self.clouds]
        ordered_clouds = ",".join(cloud_size_pairs)

        # Get a Cloud and Launch Config to feed to the domain constructor
        a_cloud = self.clouds[0]
        a_lc_name = "%s@%s" % (self.launch_config_name, a_cloud)
        a_lc_list = self.connection.get_all_launch_configurations(names=[a_lc_name, ])

        if len(a_lc_list) != 1:
            raise SystemExit("Couldn't get launch config %s" % self.launch_config_name)
        a_lc = a_lc_list[0]

        # Set how many domains we would like to start our domain with
        n_preserve_key = 'minimum_vms'
        n_preserve = 0

        # Marshall Phantom Parameters
        policy_tag = Tag(connection=self.connection, key=policy_name_key,
                         value=policy_name, resource_id=self.domain_name)
        clouds_tag = Tag(connection=self.connection, key=ordered_clouds_key,
                         value=ordered_clouds, resource_id=self.domain_name)
        npreserve_tag = Tag(connection=self.connection, key=n_preserve_key,
                            value=n_preserve, resource_id=self.domain_name)

        tags = [policy_tag, clouds_tag, npreserve_tag]

        # Remove any existing domain name with the same name
        existing_domains = self.connection.get_all_groups(names=[self.domain_name, ])
        for domain in existing_domains:
            print "Removing existing instance of domain '%s'" % domain.name
            domain.delete()

        # Create our domain
        print "Creating domain %s" % self.domain_name
        domain = AutoScalingGroup(
            availability_zones=["us-east-1"],
            connection=self.connection, group_name=self.domain_name,
            min_size=n_preserve, max_size=n_preserve, launch_config=a_lc, tags=tags)
        self.connection.create_auto_scaling_group(domain)

    def run_policy(self):

        domains = self.connection.get_all_groups(names=[self.domain_name, ])
        if len(domains) != 1:
            raise SystemExit("Couldn't get domain %s" % self.domain_name)
        domain = domains[0]

        capacity = 1
        print "set %s capacity to %s" % (self.domain_name, capacity)
        domain.set_capacity(capacity)
        time.sleep(10)

        capacity += 1
        print "set %s capacity to %s" % (self.domain_name, capacity)
        domain.set_capacity(capacity)
        time.sleep(10)

        capacity += 1
        print "set %s capacity to %s" % (self.domain_name, capacity)
        domain.set_capacity(capacity)
        time.sleep(10)

        capacity += 1
        print "set %s capacity to %s" % (self.domain_name, capacity)
        domain.set_capacity(capacity)

        print "let domain settle for 60s"
        time.sleep(60)

        capacity = 0
        print "set %s capacity back to %s" % (self.domain_name, capacity)
        domain.set_capacity(capacity)


MyPhantomDecisionEngine()

