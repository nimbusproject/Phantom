import boto
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo
import logging
import boto.ec2.autoscale
import unittest
import time
import uuid
import pyhantom
from pyhantom.main_router import MainRouter
from pyhantom.nosetests import RunTestPwFileServer

# this test has a new server ever time to make sure there is a fresh env
from pyhantom.system.tester import _TESTONLY_clear_registry

class BasicLaunchConfigTests(unittest.TestCase):

    tst_server = RunTestPwFileServer(MainRouter())

    @classmethod
    def setupClass(cls):
        print "setUpModule"
        try:
            cls.tst_server.start()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)
        time.sleep(0.5)

    @classmethod
    def teardownClass(cls):
        try:
            cls.tst_server.end()
            cls.tst_server.join()
        except Exception, ex:
            pyhantom.util.log(logging.ERROR, str(ex), printstack=True)

    def _get_good_con(self):
        region = RegionInfo('localhost')
        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=self.username, aws_secret_access_key=self.password, is_secure=False, port=self.port, debug=3, region=region)
        con.host = 'localhost'
        return con

    def setUp(self):
        (self.username, self.password, self.port) = BasicLaunchConfigTests.tst_server.get_boto_values()
        self.con = self._get_good_con()

    def tearDown(self):
        _TESTONLY_clear_registry()

    def tests_list_empty_groups(self):
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x), "Should have gotten no rows back %s | %s" % (len(x), str(x)))

    def test_create_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = self.con.create_launch_configuration(lc)
        self.assertTrue(x.request_id)

    def test_create_delete_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.delete_launch_configuration(name)
        self.assertTrue(x.request_id)

    def test_create_delete_list_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))

    def test_create_delete_list_simple(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].name, name)
        self.con.delete_launch_configuration(name)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x))

    def test_delete_failure(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.delete_launch_configuration(name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_same_twice_error(self):
        name = str(uuid.uuid4()).split('-')[0]
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = self.con.create_launch_configuration(lc)
        try:
            x = self.con.create_launch_configuration(lc)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_delete_not_there(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.delete_launch_configuration(name)
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_list_not_there(self):
        name = str(uuid.uuid4()).split('-')[0]
        try:
            x = self.con.get_all_launch_configurations(names=[name])
            self.assertTrue(False, "Should have thrown an exception")
        except BotoServerError, ex:
            pass

    def test_create_list_multiple(self):
        name1 = str(uuid.uuid4()).split('-')[0]
        name2 = str(uuid.uuid4()).split('-')[0]
        lc1 = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name1, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        lc2 = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name2, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc1)
        self.con.create_launch_configuration(lc2)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(2, len(x))
        for rc in x:
            self.assertTrue(rc.name in [name1, name2])

        self.con.delete_launch_configuration(name1)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].name, name2)
        
    def test_list_no_contig(self):
        element_count = 5
        names = []
        for i in range(0, element_count):
            name = str(uuid.uuid4()).split('-')[0]
            names.append(name)
            lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
            self.con.create_launch_configuration(lc)

        nl = [names[1], names[4]]
        x = self.con.get_all_launch_configurations(names=nl)
        for rc in x:
            self.assertTrue(rc.name in nl)

        for n in names:
            self.con.delete_launch_configuration(n)

