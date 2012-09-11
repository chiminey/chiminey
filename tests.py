import random
import unittest
from flexmock import flexmock
from cloudenable.simplepackage import _create_cloud_connection
from cloudenable.simplepackage import create_environ
from cloudenable.simplepackage import NodeState
from cloudenable import simplepackage
import logging
import logging.config


from libcloud.compute.drivers.ec2 import EucNodeDriver


class CloudTests(unittest.TestCase):

    def setUp(self):
        logging.config.fileConfig('logging.conf')

        pass

    def test_create_connection(self):

        vm_size = 100
        image_name = "ami-0000000d" #TODO: should not be hardcoded in simplepackage

        settings = flexmock(EC2_ACCESS_KEY = "",EC2_SECRET_KEY = "", VM_SIZE=vm_size,
            PRIVATE_KEY_NAME = "", SECURITY_GROUP = "", CLOUD_SLEEP_INTERVAL=0)


        # fake3 = flexmock(found = True)
        # flexmock(EucNodeDriver).new_instances(fake3)
        # self.assertEquals(_create_cloud_connection(settings).found,True)


        # don't want to call paramiko work in this testcase
        flexmock(simplepackage).should_receive('_store_md5_on_instances').and_return(0)

        fakeimage = flexmock(id=image_name)
        fakesize = flexmock(id=vm_size)
        fakenode = flexmock(name="foo",state=NodeState.RUNNING,public_ips=[1])

        fakecloud = flexmock(
            found = True,
            list_images = lambda: [fakeimage],
            list_sizes = lambda: [fakesize],
            list_nodes = lambda: [fakenode],
            create_node = lambda name,size,image,ex_keyname,ex_securitygroup: fakenode)


        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(create_environ(1,settings),None)



if __name__ == '__main__':
    unittest.main()