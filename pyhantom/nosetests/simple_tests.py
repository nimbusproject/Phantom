import boto
from boto.regioninfo import RegionInfo
import logging
import os
import boto.ec2.autoscale
import unittest
import uuid
from wsgiref.simple_server import make_server
import time
import pyhantom
from pyhantom.main_router import MainRouter
from pyhantom.nosetests import RunTestPwFileServer

# this test has a new server ever time to make sure there is a fresh env
from pyhantom.system.tester import _TESTONLY_clear_registry

class BasicUserAPITests(unittest.TestCase):

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
        (self.username, self.password, self.port) = BasicUserAPITests.tst_server.get_boto_values()
        self.con = self._get_good_con()

    def tearDown(self):
        _TESTONLY_clear_registry()

    def tests_list_empty_groups(self):
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x), "Should have gotten no rows back %s | %s" % (len(x), str(x)))

    def test_create_simple(self):
        name = "TOONSDAMEX"
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = self.con.create_launch_configuration(lc)
        self.assertTrue(x.request_id)

    def test_create_delete_simple(self):
        name = "TOONSDAMEX"
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.delete_launch_configuration(name)
        self.assertTrue(x.request_id)

    def test_create_delete_list_simple(self):
        name = "TOONSDAMEX"
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))

    def test_create_delete_list_simple(self):
        name = "TOONSDAMEX"
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(self.con, name=name, image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        self.con.create_launch_configuration(lc)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(1, len(x))
        self.assertEqual(x[0].name, name)
        self.con.delete_launch_configuration(name)
        x = self.con.get_all_launch_configurations()
        self.assertEqual(0, len(x))