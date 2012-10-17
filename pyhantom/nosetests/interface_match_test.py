import pyhantom.authz
from pyhantom.authz import PHAuthzIface
from pyhantom.system import SystemAPI
from pyhantom.phantom_exceptions import PhantomNotImplementedException
import unittest

class TestInterfaceAuthz(unittest.TestCase):

    def test_interface_errors(self):
        iface = PHAuthzIface()
        try:
            x = iface.get_user_object_by_access_id()
            self.fail("should have thrown an exception")
        except PhantomNotImplementedException:
            pass

class TestInterfaceSystem(unittest.TestCase):

    def test_interface_errors(self):

        name = "XXX"

        iface = SystemAPI()

        try:
            iface.create_launch_config(name)
        except PhantomNotImplementedException:
            pass
        try:
            iface.get_launch_configs()
        except PhantomNotImplementedException:
            pass
        try:
            iface.delete_launch_config(name)
        except PhantomNotImplementedException:
            pass
        try:
            iface.create_autoscale_group(name)
        except PhantomNotImplementedException:
            pass
        try:
            new_conf = {'alter_autoscale_group': 1}
            iface.alter_autoscale_group(name, new_conf)
        except PhantomNotImplementedException:
            pass
        try:
            iface.get_autoscale_groups()
        except PhantomNotImplementedException:
            pass
        try:
            iface.delete_autoscale_group(name)
        except PhantomNotImplementedException:
            pass
        try:
            iface.get_autoscale_instances()
        except PhantomNotImplementedException:
            pass
        try:
            iface.terminate_instances(None, "i-deadbeef", false)
        except PhantomNotImplementedException:
            pass

if __name__ == '__main__':
    unittest.main()
