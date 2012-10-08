# Copyright (C) 2012, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import random
import os
import time
import unittest
from flexmock import flexmock
import logging
import logging.config
import paramiko
import json
import sys

from cloudconnector import *
#from sshconnector import get_package_pids
from hrmcimpl import *

import cloudconnector
import sshconnector
#import hrmcimpl

#from hrmcstages import get_filesys
#from hrmcstages import get_file
#from hrmcstages import get_run_info
#from hrmcstages import get_run_info_file

from hrmcstages import get_settings


from libcloud.compute.drivers.ec2 import EucNodeDriver

logger = logging.getLogger('tests')

from smartconnector import Stage
from smartconnector import SequentialStage
#from smartconnector import SmartConnector
#from hrmcstages import Create,
from hrmcstages import Configure
from hrmcstages import Setup
from hrmcstages import Run
from hrmcstages import Finished
#from hrmcstages import Teardown

from filesystem import DataObject
from filesystem import FileSystem

#TODO: need to split up these tests into separate files in a tests directory


class CounterStage(Stage):

    def __init__(self, context):
        context['count'] = 0

    def triggered(self, context):
        count = context['count']
        return (count < 10)

    def process(self, context):

        self.count = context['count']
        self.count += 1

    def output(self, context):
        context['count'] = self.count


class TestStage(Stage):
    """ Basic stage with counter for testing """

    def __init__(self, context, key="teststage"):
        self.must_trigger = True
        self.test_count = 0
        self.key = key
        context[key] = 0

    def triggered(self, context):
        return self.must_trigger

    def process(self, context):
        pass

    def output(self, context):
        context[self.key] += 1
        pass


class ConfigureStageTests(unittest.TestCase):

    def test_simple(self):

        con = Configure()
        context = {}
        self.assertTrue(con.triggered(context), True)
        con.process(context)
        context = con.output(context)
        self.assertEquals(context.keys(), ['filesys'])
        settings = get_settings(context)
        self.assertTrue(len(settings) > 0)


class CreateStageTests(unittest.TestCase):
    # TODO:
    pass


class SetupStageTests(unittest.TestCase):
    """
    Tests the HRMC Setup Stage
    """
    HOME_DIR = os.path.expanduser("~")
    global_filesystem = os.path.join(HOME_DIR, "test_setupstagetests")
    local_filesystem = 'default'

    def setUp(self):
        logging.config.fileConfig('logging.conf')
        self.vm_size = 100
        self.image_name = "ami-0000000d"  # FIXME: is hardcoded in
                                          # simplepackage
        self.instance_name = "foo"
        self.settings = {
            'USER_NAME':  "accountname", 'PASSWORD':  "mypassword",
            'GROUP_DIR_ID': "test", 'EC2_ACCESS_KEY': "",
            'EC2_SECRET_KEY': "", 'VM_SIZE': self.vm_size,
            'VM_IMAGE': "ami-0000000d",
            'PRIVATE_KEY_NAME': "", 'PRIVATE_KEY': "", 'SECURITY_GROUP': "",
            'CLOUD_SLEEP_INTERVAL': 0, 'GROUP_ID_DIR': "", 'DEPENDS': ('a',),
            'DEST_PATH_PREFIX': "package", 'PAYLOAD_CLOUD_DIRNAME': "package",
            'PAYLOAD_LOCAL_DIRNAME': "", 'COMPILER': "g77", 'PAYLOAD': "payload",
            'COMPILE_FILE': "foo", 'MAX_SEED_INT': 100, 'RETRY_ATTEMPTS': 3,
            'OUTPUT_FILES': ['a', 'b']}

    def test_setup_simple(self):

        logger.debug("%s:%s" % (self.__class__.__name__,
                                sys._getframe().f_code.co_name))

        group_id = "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg"

        # Setup the mocks for SSH and cloud connections

        # Fake channel for communicating with server vida socket interface
        fakechan = flexmock(send=lambda str: True)
        fakechan.should_receive('recv') \
            .and_return('foo [%s@%s ~]$ ' % (self.settings['USER_NAME'],
                                             self.instance_name)) \
            .and_return('bar [root@%s %s]# ' % (self.instance_name,
                                                self.settings['USER_NAME'])) \
            .and_return('baz [%s@%s ~]$ ' % (self.settings['USER_NAME'],
                                             self.instance_name))
        fakechan.should_receive('close').and_return(True)

        #exec_mock = ["", flexmock(readlines=lambda: ["done\n"]), ""]
        # Make fake sftp connection
        fakesftp = flexmock(get=lambda x, y: True, put=lambda x, y: True)
        exec_ret = ["", flexmock(readlines=lambda: ["1\n"]),
                    flexmock(readlines=lambda: [""])]
        # Make second fake ssh connection  for the individual setup operation
        fakessh2 = flexmock(load_system_host_keys=lambda x: True,
                            set_missing_host_key_policy=lambda x: True,
                            connect=lambda ipaddress, username,
                                           password, timeout: True,
                            exec_command=lambda command: exec_ret,
                            invoke_shell=lambda: fakechan,
                            open_sftp=lambda: fakesftp)
        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient') \
            .and_return(fakessh2)
        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state2 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])
        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size, image, ex_keyname, ex_securitygroup: fakenode_state1)
        fakecloud.should_receive('list_nodes') \
            .and_return((fakenode_state2,))
        flexmock(EucNodeDriver).new_instances(fakecloud)

        # Setup fsys and initial config files for setup
        f1 = DataObject("config.sys")
        f1.create(json.dumps(self.settings))
        f2 = DataObject("runinfo.sys")
        f2.create(json.dumps({'group_id': group_id}))
        print("f2=%s" % f2)
        fs = FileSystem(self.global_filesystem, self.local_filesystem)
        fs.create(self.local_filesystem, f1)
        fs.create(self.local_filesystem, f2)
        print("fs=%s" % fs)
        context = {'filesys': fs}
        print("context=%s" % context)
        s1 = Setup()

        res = s1.triggered(context)
        print res
        self.assertEquals(res, True)
        self.assertEquals(s1.group_id, group_id)

        s1.process(context)

        s1.output(context)
        config = fs.retrieve("default/runinfo.sys")
        content = json.loads(config.retrieve())
        self.assertEquals(content,
                          {'group_id': group_id,
                           'setup_finished': 1})


class RunStageTests(unittest.TestCase):
    """
    Tests the HRMC Run Stage
    """

    HOME_DIR = os.path.expanduser("~")
    global_filesystem = os.path.join(HOME_DIR, 'test_runstageTests')
    local_filesystem = 'default'

    def setUp(self):
        logging.config.fileConfig('logging.conf')
        self.vm_size = 100
        self.image_name = "ami-0000000d"  # FIXME: is hardcoded in
                                          # simplepackage
        self.instance_name = "foo"

        self.settings = {
            'USER_NAME': "accountname", 'PASSWORD': "mypassword",
            'GROUP_DIR_ID': "test", 'EC2_ACCESS_KEY': "",
            'EC2_SECRET_KEY': "", 'VM_SIZE': self.vm_size,
            'VM_IMAGE': "ami-0000000d",
            'PRIVATE_KEY_NAME': "", 'PRIVATE_KEY': "", 'SECURITY_GROUP': "",
            'CLOUD_SLEEP_INTERVAL': 0, 'GROUP_ID_DIR': "", 'DEPENDS': ('a',),
            'DEST_PATH_PREFIX': "package", 'PAYLOAD_CLOUD_DIRNAME': "package",
            'PAYLOAD_LOCAL_DIRNAME': "", 'COMPILER': "g77", 'PAYLOAD': "payload",
            'COMPILE_FILE': "foo", 'MAX_SEED_INT': 100, 'RETRY_ATTEMPTS': 3,
            'OUTPUT_FILES': ['a', 'b']}

    def test_run(self):

        logger.debug("%s:%s" % (self.__class__.__name__,
                                sys._getframe().f_code.co_name))
        group_id = "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg"

        #TODO: copy input files into filesystem

        # Make fake sftp connection
        fakesftp = flexmock(put=lambda x, y: True)

        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda ipaddress, username,
                                        password, timeout: True,
                        exec_command=lambda command: [
                            "",
                            flexmock(readlines=lambda: ["1\n"]),
                            flexmock(readlines=lambda: [""])],
                        open_sftp=lambda: fakesftp
                        )

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size, image,
                                 ex_keyname,
                                 ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes').and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir').and_return(['inputfile1',
                                                           'inputfile2'])
        flexmock(time).should_receive('sleep')

        flexmock(EucNodeDriver).new_instances(fakecloud)

        # FIXME: This does not appear to work and is ignored.
        flexmock(sshconnector) \
            .should_receive('get_package_pids') \
            .and_return([1])

        f1 = DataObject("config.sys")
        self.settings['seed'] = 42
        f1.create(json.dumps(self.settings))
        f2 = DataObject("runinfo.sys")
        f2.create(json.dumps({'group_id': group_id, 'setup_finished': 1}))
        print("f2=%s" % f2)
        fs = FileSystem(self.global_filesystem, self.local_filesystem)
        fs.create(self.local_filesystem, f1)
        fs.create(self.local_filesystem, f2)
        print("fs=%s" % fs)
        id = "mytestid"
        context = {'filesys': fs, 'id': id}
        print("context=%s" % context)
        s1 = Run()
        res = s1.triggered(context)
        logger.debug("triggered done")
        print res
        self.assertEquals(res, True)
        self.assertEquals(s1.group_id, group_id)

        logger.debug("about to process")
        pids = s1.process(context)
        self.assertEquals(pids.values(), [['1\n']])

        logger.debug("about to output")
        s1.output(context)

        config = fs.retrieve("default/runinfo.sys")
        content = json.loads(config.retrieve())
        logger.debug("content=%s" % content)
        self.assertEquals(s1.input_dir, "input_%s" % id)

        self.assertEquals(content, {
            "runs_left": 1,
            "group_id": "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg",
            "setup_finished": 1})


class FinishedStageTests(unittest.TestCase):
    """
    Tests the HRMC Run Stage
    """

    HOME_DIR = os.path.expanduser("~")
    global_filesystem = os.path.join(HOME_DIR, "test_runstageTests")
    local_filesystem = 'default'

    def setUp(self):
        logging.config.fileConfig('logging.conf')
        self.vm_size = 100
        self.image_name = "ami-0000000d"  # FIXME: is hardcoded in
                                          # simplepackage
        self.instance_name = "foo"

        self.settings = {
            'USER_NAME': "accountname", 'PASSWORD': "mypassword",
            'GROUP_DIR_ID': "test", 'EC2_ACCESS_KEY': "",
            'EC2_SECRET_KEY': "", 'VM_SIZE': self.vm_size,
            'VM_IMAGE': "ami-0000000d",
            'PRIVATE_KEY_NAME': "", 'PRIVATE_KEY': "", 'SECURITY_GROUP': "",
            'CLOUD_SLEEP_INTERVAL': 0, 'GROUP_ID_DIR': "", 'DEPENDS': ('a',),
            'DEST_PATH_PREFIX': "package", 'PAYLOAD_CLOUD_DIRNAME': "package",
            'PAYLOAD_LOCAL_DIRNAME': "", 'COMPILER': "g77", 'PAYLOAD': "payload",
            'COMPILE_FILE': "foo", 'MAX_SEED_INT': 100, 'RETRY_ATTEMPTS': 3,
            'OUTPUT_FILES': ['a', 'b']}

    def test_finished(self):

        logger.debug("%s:%s" % (self.__class__.__name__,
                               sys._getframe().f_code.co_name))
        group_id = "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg"

        #TODO: copy input files into filesystem

        # Make fake sftp connection
        fakesftp = flexmock(get=lambda x, y: True, put=lambda x, y: True)

        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda ipaddress, username,
                                        password, timeout: True,
                        exec_command=lambda command: [
                            "",
                            flexmock(readlines=lambda: ["1\n"]),
                            flexmock(readlines=lambda: [""])],
                        open_sftp=lambda: fakesftp
                        )

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size, image, ex_keyname,
                                 ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes') \
            .and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir') \
            .and_return(['inputfile1', 'inputfile2'])
        flexmock(time).should_receive('sleep')

        flexmock(EucNodeDriver).new_instances(fakecloud)

        # FIXME: This does not appear to work and is ignored.
        flexmock(sshconnector).should_receive('get_package_pids') \
            .and_return([1])

        f1 = DataObject("config.sys")
        self.settings['seed'] = 42
        f1.create(json.dumps(self.settings))
        f2 = DataObject("runinfo.sys")
        f2.create(json.dumps({'group_id': group_id,
                              'runs_left': 1,
                              'setup_finished': 1}))
        print("f2=%s" % f2)
        fs = FileSystem(self.global_filesystem,
                        self.local_filesystem)
        fs.create(self.local_filesystem, f1)
        fs.create(self.local_filesystem, f2)
        print("fs=%s" % fs)
        id = "mytestid"
        context = {'filesys': fs, 'id': id}
        print("context=%s" % context)
        s1 = Finished()
        res = s1.triggered(context)
        logger.debug("triggered done")
        self.assertEquals(res, True)
        self.assertEquals(s1.group_id, group_id)

        self.assertEquals(s1.output_dir, "output_%s" % id)

        # # Change run_info to 0
        # run_info_file = get_run_info_file(context)
        # logger.debug("run_info_file=%s" % run_info_file)
        # run_info = get_run_info(context)
        # self.group_id = run_info['group_id']
        # run_info['runs_left'] = 0
        # run_info_text = json.dumps(run_info)
        # run_info_file.setContent(run_info_text)
        # fs.update("default", run_info_file)
        #res = s1.triggered(context)
        #logger.debug("triggered done")
        #self.assertEquals(res, False)

        logger.debug("about to process")
        s1.process(context)
        self.assertEquals(len(s1.nodes), 1)
        # FIXME: does not work due to mock problems

        #self.assertEquals(len(s1.finished_nodes),1)
        #self.assertEquals(len(s1.error_nodes),0)

        #logger.debug("about to output")
        #TODO: need to change result of next step to test
        #s1.output(context)

        #config = fs.retrieve("default/runinfo.sys")
        #content = json.loads(config.retrieve())
        #logger.debug("content=%s" % content)
        #self.assertEquals(content, {
        #    "runs_left": 1,
        #    "error_nodes":0,
        #    "group_id": group_id,
        #    "setup_finished": 1})


class FileSystemTests(unittest.TestCase):
    HOME_DIR = os.path.expanduser("~")
    global_filesystem = os.path.join(HOME_DIR, 'test_globalFS')
    local_filesystem = 'test_localFS'
    filesystem = FileSystem(global_filesystem, local_filesystem)

    def setUp(self):
        pass

    def test_create(self):
        data_object = DataObject("test_file")
        data_object_content = "hello\n" + "iman\n" + "and\n" + "seid\n"
        data_object.create(data_object_content)
        absolute_path_file = os.path.join(
            self.global_filesystem,
            self.local_filesystem, data_object.getName())
       #absolute_path_file = self.global_filesystem + "/" +  \
       # self.local_filesystem + "/"+ data_object.getName()

        self.assertEquals(data_object_content, data_object.getContent())
        self.filesystem.create(self.local_filesystem, data_object)
        self.assertTrue(os.path.exists(absolute_path_file))

    def test_retreve(self):
        file_name = "test_file"
        file_content = "hello\n" + "iman\n" + "and\n" + "seid\n"
        file_to_be_retrieved = self.local_filesystem + "/" + file_name
        retrieved_data_object = self.filesystem.retrieve(file_to_be_retrieved)
        self.assertNotEqual(retrieved_data_object, None)
        self.assertEqual(file_name, retrieved_data_object.getName())
        self.assertEqual(file_content, retrieved_data_object.getContent())

        file_name = "unknown"
        file_to_be_retrieved = self.local_filesystem + "/" + file_name
        retrieved_data_object = self.filesystem.retrieve(file_to_be_retrieved)
        self.assertEqual(retrieved_data_object, None)

    def test_update(self):
        updated_data_object = DataObject("test_file")
        updated_data_object_content = "New Greetings\niman\nand\nseid\n"
        updated_data_object.create(updated_data_object_content)

        is_updated = self.filesystem.update(self.local_filesystem,
                                            updated_data_object)
        self.assertTrue(is_updated)

        updated_data_object.setName("unknown_file")
        is_updated = self.filesystem.update(self.local_filesystem,
                                            updated_data_object)
        self.assertFalse(is_updated)

    def test_delete(self):
        data_object = DataObject("test_file_delete")
        data_object_content = "hello\n" + "iman\n" + "and\n" + "seid\n"
        data_object.create(data_object_content)

        is_created = self.filesystem.create(self.local_filesystem,
                                            data_object)
        self.assertTrue(is_created)

        file_to_be_deleted = self.local_filesystem + "/test_file_delete"
        is_deleted = self.filesystem.delete(file_to_be_deleted)
        self.assertTrue(is_deleted)
        absolute_path_file = self.global_filesystem + "/" + file_to_be_deleted
        self.assertFalse(os.path.exists(absolute_path_file))

        file_to_be_deleted = self.local_filesystem + "/unknown"
        is_deleted = self.filesystem.delete(file_to_be_deleted)
        self.assertFalse(is_deleted)

    """
     def test_simpletest(self):
        fsys = FileSystem()

        f1 = DataObject("c")
        fsys.create("a/b",f1)

        f3 = fsys.retrieve("a/b/c")
        line = f3.retrieve_line(2)
        print line

        f2 = DataObject("c")
        lines = ["hello","iman"]
        f2.create(lines)

        fsys.update("a/b",f2) #whole repace

        fsys.update("a/b/d",f2)

        fsys.delete("a/b/c")
        #assert statement
    """


class ConnectorTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_looper(self):
        """
        Creates a simple 0-10 counter from looping stage
        """

        context = {}
        s = CounterStage(context)
        while s.triggered(context):
            s.process(context)
            s.output(context)

        self.assertEquals(context['count'], 10)

    # def test_smart_connector(self):
    #     """
    #     Creates a simple smart connector
    #     """
    #     context = {}
    #     s1 = TestStage(context)
    #     ss1 = SmartConnector(s1)
    #     ss1.process(context)
    #     self.assertEquals(context,{'teststage':1})

    def test_seq_stage(self):
        """
        Creates a sequential Stage
        """
        logger.debug("here i also am")
        context = {}
        s1 = TestStage(context)
        s2 = TestStage(context)
        s3 = TestStage(context)
        s4 = TestStage(context)

        # whether we will drop out straight away or continue.

        finished = TestStage(context, "finished")

        # how to convert input to output
        convert = TestStage(context, "convert")

        ss1 = SequentialStage([s1, finished, convert,
                               s2, finished, convert,
                               s3, finished, convert,
                               s4, finished, convert])

        ss1.process(context)
        self.assertEquals(context, {'finished': 4,
                                   'convert': 4,
                                   'teststage': 4})


    # def test_daisychain(self):

    #     # each accepts a filesystem and either uses or creates subfilesystem
    #     # each accepts a context and can change as needed.
    #     context = {}

    #     s1 = Setup(context)
    #     s2 = Run(context)
    #     s3 = Finished(context)

    #     p = ParallelStage()
    #     s = SequentialStage([s1,s2,s3])


class CloudTests(unittest.TestCase):
    # TODO: Tests only the most basic run throughs of the operations with
    # single nodes. Expand to include multiple nodes, exceptions thrown
    # and return real results from paramiko and cloud calls to validate.

    def setUp(self):
        logging.config.fileConfig('logging.conf')
        self.vm_size = 100
        self.image_name = "ami-0000000d"  # FIXME: is hardcoded in
                                          # simplepackage
        self.instance_name = "foo"

        self.settings = {
            'USER_NAME': "accountname", 'PASSWORD': "mypassword",
            'GROUP_DIR_ID': "test", 'EC2_ACCESS_KEY': "",
            'EC2_SECRET_KEY': "", 'VM_SIZE': self.vm_size,
            'VM_IMAGE': "ami-0000000d",
            'PRIVATE_KEY_NAME': "", 'PRIVATE_KEY': "", 'SECURITY_GROUP': "",
            'CLOUD_SLEEP_INTERVAL': 0, 'GROUP_ID_DIR': "", 'DEPENDS': ('a',),
            'DEST_PATH_PREFIX': "package", 'PAYLOAD_CLOUD_DIRNAME': "package",
            'PAYLOAD_LOCAL_DIRNAME': "", 'COMPILER': "g77", 'PAYLOAD': "payload",
            'COMPILE_FILE': "foo", 'MAX_SEED_INT': 100, 'RETRY_ATTEMPTS': 3,
            'OUTPUT_FILES': ['a', 'b']}

    def test_create_connection(self):

        # Make fake ssh connection
        # TODO: should make multiple return values to simulate all the
        # correct input/output responses

        exec_mock = ["", flexmock(readlines=lambda: ["done\n"]),
                     flexmock(readlines=lambda: [""])]

        fakessh = flexmock(
            load_system_host_keys=lambda x: True,
            set_missing_host_key_policy=lambda x: True,
            connect=lambda ipaddress, username, password, timeout: True,
            exec_command=lambda command: exec_mock)

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.PENDING,
                                   public_ips=[1])
        fakenode_state2 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda
                name, size, image,
                ex_keyname,
                ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes') \
            .and_return((fakenode_state1,)) \
            .and_return((fakenode_state2,))

        group_id = 'acbd18db4cc2f85cedef654fccc4a4d8'
        flexmock(cloudconnector).should_receive('_generate_group_id') \
            .and_return(group_id)

        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(create_environ(1, self.settings), group_id)

    def test_setup_multi_task(self):

        logger.debug("test_setup_multi_tasks")

        group_id = "sq42kdjshasdkjghauiwytuiawjmkghasjkghasg"

        # Fake channel for communicating with server vida socket interface
        fakechan = flexmock(send=lambda str: True)
        fakechan.should_receive('recv') \
            .and_return('foo [%s@%s ~]$ ' % (self.settings['USER_NAME'],
                                             self.instance_name)) \
            .and_return('bar [root@%s %s]# ' % (self.instance_name,
                                                self.settings['USER_NAME'])) \
            .and_return('baz [%s@%s ~]$ ' % (self.settings['USER_NAME'],
                                             self.instance_name))
        fakechan.should_receive('close').and_return(True)

        exec_mock = ["", flexmock(readlines=lambda: ["done\n"]),
                     flexmock(readlines=lambda: [""])]

        # Make fake ssh connection
        fakessh1 = flexmock(
            load_system_host_keys=lambda x: True,
            set_missing_host_key_policy=lambda x: True,
            connect=lambda ipaddress, username, password, timeout: True,
            exec_command=lambda command: exec_mock)

        # Make fake sftp connection
        fakesftp = flexmock(get=lambda x, y: True, put=lambda x, y: True)

        exec_ret = ["", flexmock(readlines=lambda: ["1\n"]),
                    flexmock(readlines=lambda: [""])]
        # Make second fake ssh connection  for the individual setup operation
        fakessh2 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda
                            ipaddress, username,
                            password, timeout: True,
                        exec_command=lambda command: exec_ret,
                        invoke_shell=lambda: fakechan,
                        open_sftp=lambda: fakesftp)

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient') \
            .and_return(fakessh1) \
            .and_return(fakessh2)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.PENDING,
                                   public_ips=[1])
        fakenode_state2 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda
                        name, size, image, ex_keyname,
                        ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes') \
            .and_return((fakenode_state1,)) \
            .and_return((fakenode_state2,))

        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(setup_multi_task(group_id, self.settings), None)

    def test_prepare_multi_input(self):

        logger.debug("test_prepare_multi_input")

        # Make fake sftp connection
        fakesftp = flexmock(put=lambda x, y: True)

        exec_ret = ["", flexmock(readlines=lambda: ["1\n"]),
                    flexmock(readlines=lambda: [""])]
        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda
                            ipaddress, username,
                            password, timeout: True,
                        exec_command=lambda command: exec_ret,
                        open_sftp=lambda: fakesftp)

        flexmock(random).should_receive('randrange').and_return(42)

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo", state=NodeState.RUNNING,
                                   public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size, image, ex_keyname,
                                 ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes').and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir').and_return(['mydirectory'])

        flexmock(EucNodeDriver).new_instances(fakecloud)

        self.assertEquals(prepare_multi_input("foobar",
                                              "",
                                              self.settings,
                                              None),
                          None)

    def test_run_multi_task(self):
        logger.debug("test_run_multi_task")

        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda ipaddress, username, password, timeout: True,
                        exec_command=lambda command: [
                            "",
                            flexmock(readlines=lambda: ["1\n"]),
                            flexmock(readlines=lambda: [""])],
                        )

        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)

        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                 state=NodeState.RUNNING,
                                 public_ips=[1])

        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size,
                                 image, ex_keyname,
                                 ex_securitygroup: fakenode_state1)

        fakecloud.should_receive('list_nodes').and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir').and_return(['mydirectory'])
        flexmock(time).should_receive('sleep')

        flexmock(EucNodeDriver).new_instances(fakecloud)

        flexmock(sshconnector).should_receive('get_package_pids') \
            .with_args(fakessh1, "command") \
            .and_return([99]) \
            .and_return(None) \
            .and_return([99])

        res = run_multi_task("foobar", "", self.settings)
        #TODO: this test case fails?
        self.assertEquals(res.values(), [['1\n']])

    def test_packages_complete(self):
        logger.debug("test_packages_complete")
        # Make fake sftp connection
        fakesftp = flexmock(get=lambda x, y: True, put=lambda x, y: True)
        exec_ret = ["", flexmock(readlines=lambda: ["1\n"]),
                    flexmock(readlines=lambda: [""])]
        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda ipaddress, username,
                                       password, timeout: True,
                        exec_command=lambda command: exec_ret,
                        open_sftp=lambda: fakesftp)
        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)
        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])
        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size, image,
                               ex_keyname,
                               ex_securitygroup: fakenode_state1)
        fakecloud.should_receive('list_nodes').and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir').and_return(['mydirectory'])
        flexmock(time).should_receive('sleep')
        flexmock(EucNodeDriver).new_instances(fakecloud)
        flexmock(sshconnector).should_receive('get_package_pids') \
            .and_return(None)
        res = packages_complete("foobar", "", self.settings)
        #TODO: this test case fails
        #self.assertEquals(res, True)

    def test_collect_instances(self):
        logger.debug("test_collect_instances")
        # Make fake sftp connection
        fakesftp = flexmock(get=lambda x, y: True, put=lambda x, y: True)
        exec_ret = ["", flexmock(readlines=lambda: ["1\n"]),
                    flexmock(readlines=lambda: [""])]

        # Make fake ssh connection
        fakessh1 = flexmock(load_system_host_keys=lambda x: True,
                        set_missing_host_key_policy=lambda x: True,
                        connect=lambda ipaddress, username,
                                       password, timeout: True,
                        exec_command=lambda command: exec_ret,
                        open_sftp=lambda: fakesftp)
        # and use fake for paramiko
        flexmock(paramiko).should_receive('SSHClient').and_return(fakessh1)
        # Make fake cloud connection
        fakeimage = flexmock(id=self.image_name)
        fakesize = flexmock(id=self.vm_size)
        fakenode_state1 = flexmock(name="foo",
                                   state=NodeState.RUNNING,
                                   public_ips=[1])
        fakecloud = flexmock(
            found=True,
            list_images=lambda: [fakeimage],
            list_sizes=lambda: [fakesize],
            create_node=lambda name, size,
                               image, ex_keyname,
                               ex_securitygroup: fakenode_state1)
        fakecloud.should_receive('list_nodes').and_return((fakenode_state1,))
        flexmock(os).should_receive('listdir').and_return(['mydirectory'])
        flexmock(time).should_receive('sleep')
        flexmock(EucNodeDriver).new_instances(fakecloud)
        flexmock(sshconnector).should_receive('get_package_pids') \
            .and_return(None)
        res = collect_instances(self.settings, group_id="foobar")
        logger.debug("res= %s" % res)
        self.assertEquals(len(res), 1)
        self.assertEquals(res[0].name, "foo")
        res = collect_instances(self.settings, instance_id=self.instance_name)
        self.assertEquals(len(res), 1)
        self.assertEquals(res[0].name, "foo")
        res = collect_instances(self.settings, all_VM=True)
        self.assertEquals(len(res), 1)
        self.assertEquals(res[0].name, "foo")

    def test_destroy_environ(self):
        logger.debug("test_destroy_environ")
        # first node starts terminated, and second is there after one check
        fakenode1 = flexmock(name="foo",
                             state=NodeState.TERMINATED,
                             public_ips=[1])
        fakenode2_state1 = flexmock(name="foo",
                                    state=NodeState.RUNNING, public_ips=[1])
        fakenode2_state2 = flexmock(name="foo",
                                    state=NodeState.TERMINATED,
                                    public_ips=[1])

        fakecloud = flexmock(
            found=True,
            destroy_node=lambda instance:  True)
        fakecloud.should_receive('list_nodes') \
            .and_return([fakenode1, fakenode2_state1]) \
            .and_return([fakenode1, fakenode2_state2])
        flexmock(EucNodeDriver).new_instances(fakecloud)
        flexmock(sshconnector).should_receive('get_package_pids') \
            .and_return(None)
        res = destroy_environ(self.settings, [fakenode1, fakenode2_state1])

        self.assertEquals(res, None)


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    unittest.main()
