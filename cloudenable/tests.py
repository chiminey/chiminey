import random
import unittest
from flexmock import flexmock
from simplepackage import _create_cloud_connection
from simplepackage import setup_multi_task
from simplepackage import create_environ
from simplepackage import NodeState
import simplepackage
import logging
import logging.config
import paramiko

logger = logging.getLogger(__name__)



from libcloud.compute.drivers.ec2 import EucNodeDriver


class CloudTests(unittest.TestCase):

    def setUp(self):
        logging.config.fileConfig('logging.conf')

        pass

    def test_create_connection(self):

        vm_size = 100
        image_name = "ami-0000000d" #TODO: should not be hardcoded in simplepackage

        # Mak fake settings
        settings = flexmock(USER_NAME = "accountname", PASSWORD="mypassword",
                            GROUP_DIR_ID = "test", EC2_ACCESS_KEY = "",
                            EC2_SECRET_KEY = "", VM_SIZE=vm_size,
                            PRIVATE_KEY_NAME = "", PRIVATE_KEY="", SECURITY_GROUP = "",
                            CLOUD_SLEEP_INTERVAL=0, GROUP_ID_DIR="")

        # Make fake ssh connection
        # TODO: should make multiple return values to simulate all the correct input/output responses
        fakessh = flexmock(load_system_host_keys= lambda x: True,
                        set_missing_host_key_policy= lambda x: True,
                        connect= lambda ipaddress, username, password, timeout: True,
                        exec_command = lambda command: ["",flexmock(readlines = lambda: ["done\n"]),""])

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh)

        # Make fake cloud connection
        fakeimage = flexmock(id=image_name)
        fakesize = flexmock(id=vm_size)
        fakenode_state1 = flexmock(name="foo",state=NodeState.PENDING,public_ips=[1])
        fakenode_state2 = flexmock(name="foo",state=NodeState.RUNNING,public_ips=[1])

        fakecloud = flexmock(
            found = True,
            list_images = lambda: [fakeimage],
            list_sizes = lambda: [fakesize],
            create_node = lambda name,size,image,ex_keyname,ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes').and_return(fakenode_state1).and_return(fakenode_state2)

        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(create_environ(1,settings),None)

    def test_setup_multi_task(self):

        logger.debug("test_setup_multi_tasks")
        vm_size = 100
        image_name = "ami-0000000d" #TODO: should not be hardcoded in simplepackage
        instance_name = "foo"

        settings = flexmock(USER_NAME = "accountname", PASSWORD="mypassword",
            GROUP_DIR_ID = "test", EC2_ACCESS_KEY = "",
            EC2_SECRET_KEY = "", VM_SIZE=vm_size,
            PRIVATE_KEY_NAME = "", PRIVATE_KEY="", SECURITY_GROUP = "",
            CLOUD_SLEEP_INTERVAL=0, GROUP_ID_DIR="", DEPENDS = ('a',),
            DEST_PATH_PREFIX="package",PAYLOAD_CLOUD_DIRNAME="package",
            PAYLOAD_LOCAL_DIRNAME="", COMPILER="g77", PAYLOAD="payload", COMPILE_FILE="foo")

        group_id = "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg"

        # Fake channel for communicating with server vida socket interface
        fakechan = flexmock(send = lambda str: True)
        fakechan.should_receive('recv') \
            .and_return('foo [%s@%s ~]$ ' % (settings.USER_NAME, instance_name)) \
            .and_return('bar [root@%s %s]# ' % (instance_name,settings.USER_NAME)) \
            .and_return('baz [%s@%s ~]$ ' % (settings.USER_NAME, instance_name))
        fakechan.should_receive('close').and_return(True)


        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys= lambda x: True,
                        set_missing_host_key_policy= lambda x: True,
                        connect= lambda ipaddress, username, password, timeout: True,
                        exec_command = lambda command: ["",flexmock(readlines = lambda: ["exists\n"]),""])

        # Make fake sftp connection
        fakesftp = flexmock(get = lambda x,y: True, put = lambda x,y: True )

        # Make second fake ssh connection  for the individual setup operation
        fakessh2 = flexmock(load_system_host_keys= lambda x: True,
                        set_missing_host_key_policy= lambda x: True,
                        connect= lambda ipaddress, username, password, timeout: True,
                        exec_command = lambda command: ["",flexmock(readlines = lambda: ["exists\n"]),""],
                        invoke_shell = lambda: fakechan,
                        open_sftp = lambda: fakesftp)

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1).and_return(fakessh2)

        # Make fake cloud connection
        fakeimage = flexmock(id=image_name)
        fakesize = flexmock(id=vm_size)
        fakenode_state1 = flexmock(name="foo",state=NodeState.PENDING,public_ips=[1])
        fakenode_state2 = flexmock(name="foo",state=NodeState.RUNNING,public_ips=[1])


        fakecloud = flexmock(
            found = True,
            list_images = lambda: [fakeimage],
            list_sizes = lambda: [fakesize],
            create_node = lambda name,size,image,ex_keyname,ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes').and_return(fakenode_state1).and_return(fakenode_state2)

        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(setup_multi_task(group_id,settings),None)


if __name__ == '__main__':
    unittest.main()