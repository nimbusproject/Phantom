import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import logging
import boto.ec2.autoscale
import os
import tempfile
import unittest
import time
import uuid
import pyhantom
from pyhantom.main_router import MainRouter
from pyhantom.nosetests.server import RunPwFileLocalLCServer

class BasicAutoScaleGroupTests(unittest.TestCase):


    def _get_good_con(self):
        region = RegionInfo('localhost')
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=self.username, aws_secret_access_key=self.password, is_secure=False, port=self.port, debug=3, region=region)
        con.host = 'localhost'
        return con

    def setUp(self):
        (osf, self.db_fname) = tempfile.mkstemp(prefix="/tmp/phantom")
        db_url = "sqlite:///%s" % (self.db_fname)
        try:
            self.tst_server = RunPwFileLocalLCServer(MainRouter(), db_url)
            self.tst_server.start()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)
            raise
        time.sleep(1.5)
        (self.username, self.password, self.port) = self.tst_server.get_boto_values()
        self.con = self._get_good_con()

    def tearDown(self):
        try:
            self.tst_server.end()
            self.tst_server.join()
            os.remove(self.db_fname)
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)
            raise ex

    def _get_lc(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        return lc

    def test_create_group_no_lc(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        try:
            asg = boto.ec2.autoscale.group.AutoScalingGroup(connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)
        except BotoServerError, ex:
            pass

    def test_create_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        lc = self._get_lc()
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5, )
        self.con.create_auto_scaling_group(asg)

    def test_create_delete_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        lc = self._get_lc()
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        self.con.delete_auto_scaling_group(group_name)

    def test_delete_nonexistant_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        try:
            self.con.delete_auto_scaling_group(group_name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_group_twice(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        lc = self._get_lc()
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        try:
            self.con.create_auto_scaling_group(asg)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_delete_group_twice(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        lc = self._get_lc()
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        self.con.delete_auto_scaling_group(group_name)
        try:
            self.con.delete_auto_scaling_group(group_name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_list_delete_group(self):
        group_name = str(uuid.uuid4()).split('-')[0]
        lc = self._get_lc()
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        l = self.con.get_all_groups()
        self.assertEqual(l[0].name, group_name)
        self.con.delete_auto_scaling_group(group_name)

    def test_list_empty(self):
        l = self.con.get_all_groups()
        self.assertEqual(len(l), 0)

    def test_list_no_contig(self):
        lc = self._get_lc()
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        nl = [names[1], names[4]]
        x = self.con.get_all_groups(names=nl)
        for rc in x:
            self.assertTrue(rc.name in nl)

        for n in names:
            self.con.delete_auto_scaling_group(n)


    def test_list_many_asgs(self):
        lc = self._get_lc()
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        x = self.con.get_all_groups()
        self.assertEqual(len(x), len(names))
        for rc in x:
            self.assertTrue(rc.name in names)

        for n in names:
            self.con.delete_auto_scaling_group(n)

    def test_list_many_asgs_many_times(self):
        lc = self._get_lc()
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=name, availability_zones=["us-east-1"], min_size=1, max_size=5)
            self.con.create_auto_scaling_group(asg)

        for i in range(0, 8):
            x = self.con.get_all_groups()
            self.assertEqual(len(x), len(names))
        for rc in x:
            self.assertTrue(rc.name in names)

        for n in names:
            self.con.delete_auto_scaling_group(n)


    def test_set_desired_capacity(self):
        lc = self._get_lc()
        group_name = str(uuid.uuid4()).split('-')[0]
        asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=self.con, group_name=group_name, availability_zones=["us-east-1"], min_size=1, max_size=5)
        self.con.create_auto_scaling_group(asg)
        l = self.con.get_all_groups(names=[group_name])

        c = 10
        asg.set_capacity(c)

        l = self.con.get_all_groups(names=[group_name])
        self.assertEqual(c, l[0].desired_capacity)

        self.assertEqual(l[0].name, group_name)
        self.con.delete_auto_scaling_group(group_name)


