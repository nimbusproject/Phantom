import boto
import os
import tempfile
import unittest
import uuid
from wsgiref.simple_server import make_server
from pyhantom.main_router import MainRouter

class BasicUserAPITests(unittest.TestCase):

    def setUp(self):
        (osf, self.fname) = tempfile.mkstemp()
        os.close(osf)
        self.username = str(uuid.uuid4())
        self.password = str(uuid.uuid4())
        fptr = open(self.fname, "w")
        fptr.write(self.username + '\n')
        fptr.write(self.password + '\n')
        fptr.close()

        srv = make_server('localhost', 8080, MainRouter())
        srv.serve_forever()


    def tearDown(self):
        os.remove(self.fname)

    def tests_list_groups(self):

        con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_key, is_secure=is_secure, port=port, debug=debug, path=path, region=region)

        if region:
            con.host = url_parts.hostname
        #con.get_all_groups()
        
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name="XXTOONAME", image_id="ami-2b9b5842", key_name="ooi", security_groups=['default'], user_data="XXXUSERDATAYYY", instance_type='m1.small')
        x = con.create_launch_configuration(lc)
