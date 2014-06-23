# Copyright (C) 2014, RMIT University

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

import shutil
import os
from django.test import SimpleTestCase

import logging
from pprint import pformat
from collections import namedtuple
from copy import deepcopy

import boto
import paramiko
import httpretty
from mock import Mock

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from django.core.files.base import ContentFile

from chiminey import messages
from chiminey.runsettings import getval
from chiminey.smartconnectorscheduler import models
from chiminey.smartconnectorscheduler import jobs
from chiminey.initialisation import chimineyinitial
from chiminey.smartconnectorscheduler import views as schedule_views
from chiminey.examples.randomnumbers.initialise import RandomNumbersInitial
from chiminey.smartconnectorscheduler.management.commands.createuser import Command as CreateUserCommand
from chiminey.smartconnectorscheduler import tasks

from chiminey.storage import storage

from chiminey.storage.storage import LocalStorage

logger = logging.getLogger(__name__)


# class LocalTestStorage(InMemoryStorage):

#     def __init__(self, location=None, base_url=None):
#         super(LocalTestStorage, self).__init__(filesystem=None)

#     def get_available_name(self, name):
#         """
#         Returns a filename that's free on the target storage system, and
#         available for new content to be written to.
#         """
#         if self.exists(name):
#             self.delete(name)
#         return name


# class RemoteTestStorage(InMemoryStorage):
#     def __init__(self, settings=None, base_url=None):
#         super(RemoteTestStorage, self).__init__(filesystem=None)

#     def get_available_name(self, name):
#         """
#         Returns a filename that's free on the target storage system, and
#         available for new content to be written to.
#         """
#         if self.exists(name):
#             self.delete(name)
#         return name


class RandomNumbersTest(SimpleTestCase):

    SCHEMA_PREFIX = "http://rmit.edu.au/schemas"
    USERNAME = "bob"
    EMAIL = "bob@bob.com"
    PASSWORD = "password"

    options = {
        'interactive': False,
        'username': USERNAME,
        'email': EMAIL,
        'password': PASSWORD,
        'remotefsys': 'unused',
        'verbosity': 0,
        'returnuser': True,
        }

    FILESYS_ROOT_PATH = os.path.join(settings.LOCAL_FILESYS_ROOT_PATH, USERNAME)

    CLOUD_COMP_PLATFORM = "mycloudcompute"
    INPUT_PLATFORM = "myinput"
    OUTPUT_PLATFORM = "myoutput"
    MYTARDIS_PLATFORM = "mymytardis"
    ROOT_DIR = "/home/centos"

    PARAMETERS = [{'name': MYTARDIS_PLATFORM,
            'root': ROOT_DIR,
            'namespace':  SCHEMA_PREFIX + "/platform/storage/mytardis",
            'parameters': {'platform_type': 'mytardis',
                            'platform_name': MYTARDIS_PLATFORM,
                            'ip_address': '',
                            'ip_address': 'acme.com',
                            'username': 'coyote',
                            'password': 'foobar'
                       }
        },
        {'name': OUTPUT_PLATFORM,
            'root': ROOT_DIR,
            'namespace':  SCHEMA_PREFIX + "/platform/storage/unix",
            'parameters': {'platform_type': 'unix',
                            'platform_name': OUTPUT_PLATFORM,
                            'ip_address': '',
                            'username': '',
                            'password': ''
                           }
                },
        {'name': CLOUD_COMP_PLATFORM,
            'root': ROOT_DIR,
            'namespace':  SCHEMA_PREFIX + "/platform/computation/cloud/ec2-based",
            'parameters': {'platform_type': 'nectar',
                            'platform_name': CLOUD_COMP_PLATFORM,
                            'ec2_access_key': 'jdksghaskjghadjksghadskjhgadg',
                            'ec2_secret_key': 'jadfhgajkghadjkfhgakluyarueiwy',
                            'private_key': "mykey",
                            'private_key_path': "/", # need location known to exist
                            'vm_image_size': 'm1.small',
                            'security_group': "mysecuritygroup"

                           }
        },

        ]

    CREATED_NODES = [['1', '127.0.0.1', u'here', 'running'],
        ['2', '127.0.0.2', u'here', 'running']]
    BOOTSTRAPPED_NODES = [['1', '127.0.0.1', u'here', 'running'],
            ['2', '127.0.0.2', u'here', 'running']]
    BOOTSTRAP_COMPLETE_MESSAGE = 'Environment Setup Completed'

    def setUp(self):
        logger.debug("setup")
        try:
            shutil.rmtree(os.path.join(
            settings.LOCAL_FILESYS_ROOT_PATH))
        except OSError:
            pass

    def tearDown(self):
        pass

    def _create_directive(self):
        directive = RandomNumbersInitial()
        directive.define_directive(
                   'randomnumbers', description='RandomNumbers', sweep=True)
        return directive

    def _execute_stages(self, context_id, correct_results):
        run_context = models.Context.objects.get(id=context_id)

        stage = run_context.current_stage
        children = models.Stage.objects.filter(parent=stage)
        if children:
            stageset = children
        else:
            stageset = [stage]

        logger.debug("stageset=%s", stageset)
        profile = run_context.owner
        logger.debug("profile=%s" % profile)

        run_settings = run_context.get_context()
        logger.debug("retrieved run_settings=%s" % pformat(run_settings))

        user_settings = {}

        triggered = 0
        for current_stage in stageset:

            logger.debug("checking stage %s for trigger" % current_stage.name)
            # get the actual stage object
            try:
                stage = jobs.safe_import(current_stage.package, [],
                {'user_settings': deepcopy(user_settings)})  # obviously need to cache this
            except ImproperlyConfigured, e:
                logger.error(e)
                messages.error(run_settings, "0: internal error (%s stage):%s"
                     % (str(current_stage.name), e))
                raise

            logger.debug("process stage=%s", stage)

            task_run_settings = deepcopy(run_settings)
            logger.debug("starting task settings = %s" % pformat(task_run_settings))
            # stage_settings are read only as transfered into context here
            stage_settings = current_stage.get_settings()
            logger.debug("stage_settings=%s" % stage_settings)

            task_run_settings = jobs.transfer(task_run_settings, stage_settings)
            logger.debug("task run_settings=%s" % task_run_settings)

            logger.debug("Stage '%s' testing for triggering" % current_stage.name)

            result = all([correct_results[x][0](task_run_settings)
                 for x in correct_results.keys() if x == current_stage.name])
            logger.debug("pre_result=%s" % result)
            self.assertTrue(result)

            try:
                if stage.is_triggered(deepcopy(task_run_settings)):
                    logger.debug("Stage '%s' TRIGGERED" % current_stage.name)
                    stage.process(deepcopy(task_run_settings))
                    task_run_settings = stage.output(task_run_settings)
                    logger.debug("updated task_run_settings=%s"
                                 % pformat(task_run_settings))
                    run_context.update_run_settings(task_run_settings)
                    logger.debug("task_run_settings=%s" % pformat(task_run_settings))
                    logger.debug("context run_settings=%s" % pformat(run_context))
                    triggered = True
                    result = all([correct_results[x][1](task_run_settings)
                         for x in correct_results.keys() if x == current_stage.name])
                    logger.debug("post_result=%s" % result)
                    logger.debug("correct_results=%s" % correct_results)
                    self.assertTrue(result)
                    break
                else:
                    logger.debug("Stage '%s' NOT TRIGGERED" % current_stage.name)
            except Exception, e:
                file_info = ""
                logger.error("0: internal error (%s stage):%s %s"
                             % (str(current_stage.name), e, file_info))
                raise
        if not triggered:
            logger.debug("No corestages is_triggered")
            run_context.deleted = True
            run_context.save()

    def _make_platforms(self, user_profile):

        for info in self.PARAMETERS:
            p = models.Platform(name=info['name'], root_path=info['root'])
            logger.debug("p.name=%s" % p.name)

            p.save()
            schema = models.Schema.objects.get(namespace=info['namespace'])
            logger.debug("schema.namespace=%s" % schema.namespace)
            pps = models.PlatformParameterSet(name=p.name,
                                              owner=user_profile,
                                              schema=schema)
            pps.save()
            for pinfok, pinfov in info['parameters'].items():
                logger.debug("pinfok=%s pinfov=%s" % (pinfok, pinfov))
                pp_name = models.ParameterName.objects.get(schema=schema,
                                                           name=pinfok)
                pp = models.PlatformParameter(name=pp_name, paramset=pps,
                                              value=pinfov)
                pp.save()

    def test_basicrun(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        try:
            shutil.copytree(os.path.join(curr_dir, "..", "payload_randnum"),
             os.path.join(settings.LOCAL_FILESYS_ROOT_PATH, "my_payloads", "payload_randnum"))
        except OSError:
            raise

        # Initialise Chiminey db
        chimineyinitial.initialise()

        # Create a user
        createuser_command = CreateUserCommand()
        user_profile = createuser_command.handle(**self.options)

        # Create a local storage for tests
        ls2 = LocalStorage(location=os.path.join(self.FILESYS_ROOT_PATH, self.USERNAME))
        logger.debug("ls2=%s" % ls2)
        ls2.save('local/payload_randnum/file1.txt', ContentFile('testing'))
        logger.debug("ls2=%s" % ls2)

        self.assertEqual(ls2.listdir(''), (['local'], []))
        self.assertEqual(ls2.listdir('local/'), (['payload_randnum'], []))
        self.assertEqual(ls2.listdir('local/payload_randnum/'), ([], ['file1.txt']))
        self.assertEqual(ls2.open('local/payload_randnum/file1.txt').read(), 'testing')

        # Map the remotestorage back to localstorage for testing
        rs = Mock()
        rs.return_value = LocalStorage(location=os.path.join(self.FILESYS_ROOT_PATH, self.USERNAME))
        storage.RemoteStorage = rs

        rs2 = storage.RemoteStorage()
        self.assertEqual(rs2.listdir(''), (['local'], []))
        self.assertEqual(rs2.listdir('local/'), (['payload_randnum'], []))
        self.assertEqual(rs2.listdir('local/payload_randnum'), ([], ['file1.txt']))
        self.assertEqual(rs2.open('local/payload_randnum/file1.txt').read(), 'testing')

        # Setup initial platforms
        self._make_platforms(user_profile)

        # Create randomnumbers directive
        directive = self._create_directive()
        Bundle = namedtuple('bundle', ['data'])
        bundle = Bundle(data={
            "smart_connector": 'hrmc',
             self.SCHEMA_PREFIX + "/bdp_userprofile/username": self.USERNAME,
             self.SCHEMA_PREFIX + "/input/system/compplatform/cloud/computation_platform": self.CLOUD_COMP_PLATFORM + "/compdir",
             self.SCHEMA_PREFIX + "/input/location/output/output_location": self.OUTPUT_PLATFORM + "/output",
             self.SCHEMA_PREFIX + "/input/mytardis/curate_data": True,
             self.SCHEMA_PREFIX + "/input/mytardis/mytardis_platform": self.MYTARDIS_PLATFORM,
             self.SCHEMA_PREFIX + "/input/mytardis/experiment_id": 0,
             self.SCHEMA_PREFIX + "/input/system/cloud/minimum_number_vm_instances": 1,
             self.SCHEMA_PREFIX + "/input/system/cloud/number_vm_instances": 4,
             self.SCHEMA_PREFIX + "/sch1/val": 1,
             self.SCHEMA_PREFIX + "/sch1/val2": 2})
        (myplatform, directive.name, directive_args, system_settings) = \
            schedule_views._post_to_directive(bundle, "randomnumbers")

        # Make new job
        (run_settings, command_args, run_context) \
             = jobs.make_runcontext_for_directive(
             myplatform,
             directive.name,
             directive_args, system_settings, self.USERNAME)
        logger.debug("run_settings=%s" % run_settings)
        logger.debug("command_args=%s" % command_args)
        logger.debug("run_context=%s" % run_context)

        # Mock out nectar cloud via boto
        instance_set = Mock(name="instance_set")
        instances = []
        for node in self.CREATED_NODES:
            instance = Mock(name="instance%s" % node[0])
            instance.id = str(node[0])
            instance.ip_address = node[1]
            #instance.ip_address = "127.0.0.2"
            instance.region = node[2]
            instance.state = node[3]
            instance.update.return_value = True
            instances.append(instance)
        instance_set.instances = instances
        logger.debug("instances=%s" % instances)
        get_instance_mock = Mock(name="get_instance_mock")
        get_instance_mock.run_instances.return_value = instance_set
        # get_instance_mock.get_all_instances.return_value = instance_set

        def get_instance_mock_reservations(*args, **kwargs):
            logger.debug("kwargs=%s" % kwargs)
            if not 'instance_ids' in kwargs.keys():
                m = [instance_set]
            elif kwargs['instance_ids'] == ["1"]:
                m = Mock(name="instances[0]")
                n = Mock(name="n[0]")
                n.instances = [instance_set.instances[0]]
                m = [n]
                logger.debug("m=%s" % m)
                logger.debug("m.instances=%s" % m[0].instances)
            elif kwargs['instance_ids'] == ["2"]:
                m = Mock(name="instances[1]")
                n = Mock(nane="n[1]")
                n.instances = [instance_set.instances[1]]
                m = [n]
                logger.debug("m=%s" % m)
                logger.debug("m.instances=%s" % m[0].instances)
            else:
                m = [instance_set]
            return m

        get_instance_mock.get_all_instances.side_effect = get_instance_mock_reservations
        connection_mock = Mock(name="connection_mock")
        connection_mock.return_value = get_instance_mock
        region_mock = Mock(name="region_mock")
        region_mock.name = "myregion"
        region_mock2 = Mock(name="region_mock2")
        region_mock2.return_value = region_mock
        boto.ec2.regioninfo.RegionInfo = region_mock2
        rtest = region_mock2()
        self.assertEqual(rtest.name, "myregion")
        boto.connect_ec2 = connection_mock
        ctest = connection_mock()
        self.assertEqual(ctest.run_instances().instances[0].id, "1")
        self.assertEqual(ctest.run_instances().instances[1].id, "2")
        self.assertEqual(len(ctest.get_all_instances()), 1)
        self.assertEqual(len(ctest.get_all_instances()[0].instances), 2)
        self.assertEqual(ctest.get_all_instances()[0].instances[0].id, "1")
        self.assertEqual(ctest.get_all_instances()[0].instances[1].id, "2")
        self.assertEqual(len(ctest.get_all_instances(instance_ids=["1"])[0].instances), 1)
        self.assertEqual(len(ctest.get_all_instances(instance_ids=["2"])[0].instances), 1)
        self.assertEqual(len(ctest.get_all_instances(instance_ids=["3"])[0].instances), 2)
        self.assertEqual(len(ctest.get_all_instances(foo=["1"])[0].instances), 2)

        # Mock out ssh via paramiko
        ss_client_mocked = Mock(name="ss_client_mocked")
        ss_client_mocked.load_system_host_keys.return_value = True
        ss_client_mocked.set_missing_host_key_policy.return_value = True
        pm1 = Mock(name="pm1")
        pm1.readlines.return_value = []
        pm2 = Mock(name="pm2")
        pm2.readlines.return_value = [self.BOOTSTRAP_COMPLETE_MESSAGE]
        pm3 = Mock(name="pm3")
        pm3.readlines.return_value = []
        ss_client_mocked.exec_command.return_value = (pm1, pm2, pm3)
        ss_client_mocked.connect.return_value = True
        ssh_client_ctor_mock = Mock(name="ssh_client_ctor_mock")
        ssh_client_ctor_mock.return_value = ss_client_mocked
        paramiko.SSHClient = ssh_client_ctor_mock
        paramiko.RSAKey.from_private_key_file = Mock(return_value=True)

        (test_pm1, test_pm2, test_pm3) = ssh_client_ctor_mock().exec_command()
        self.assertEquals(test_pm1.readlines(), pm1.readlines.return_value)
        self.assertEquals(test_pm2.readlines(), pm2.readlines.return_value)
        self.assertEquals(test_pm3.readlines(), pm3.readlines.return_value)
        # Mock out storage

        # local_storage_mock = Mock(name="localstorage")
        # m1 = Mock(name="m1")
        # # m1.listdir.return_value = ["/localtestdir1", "/localtestdir2"]

        # def get_dirs1(*args, **kwargs):
        #     logger.debug("kwargs=%s" % kwargs)
        #     return [[], ["file1.txt", "file2.txt"]]

        # m1.listdir.side_effect = get_dirs1

        # m1.save.return_value = "mylocal dest path"
        # local_storage_mock.return_value = m1
        # fp_mock = Mock(name="fp")
        # fp_mock.read.return_value = "local read content"
        # local_storage_mock.return_value.open.return_value = fp_mock
        # storage.LocalStorage = local_storage_mock
        # s = storage.LocalStorage()
        # self.assertEqual(s.open().read(), "local read content")
        # # self.assertEqual(s.listdir(), ['/localtestdir1', '/localtestdir2'])
        # self.assertEqual(s.save(), "mylocal dest path")
        # logger.debug("localstorage=%s" % s.save())

        # remote_storage_mock = Mock(name="remotestorage")
        # m2 = Mock(name="m2")

        # def get_dirs2(*args, **kwargs):
        #     logger.debug("kwargs=%s" % kwargs)
        #     return [[], ["file1.txt", "file2.txt"]]

        # m1.listdir.side_effect = get_dirs2
        # # m2.listdir.return_value = ['/remotetestdir1', '/remotetestdir2']
        # m2.save.return_value = "myremote dest path"
        # remote_storage_mock.return_value = m2
        # fp_mock2 = Mock(name="fp2")
        # fp_mock2.read.return_value = "remote read content"
        # remote_storage_mock.return_value.open.return_value = fp_mock2
        # remote_storage_mock.return_value = m2
        # storage.RemoteStorage = remote_storage_moc
        # s = storage.RemoteStorage()
        # self.assertEqual(s.open().read(), "remote read content")
        # # self.assertEqual(s.listdir(), ['/remotetestdir1', '/remotetestdir2'])
        # self.assertEqual(s.save(), "myremote dest path")
        # logger.debug("remotestorage=%s" % s.save())

        # Mock out messages api
        tasks.context_message.delay = Mock(return_value=True)
        self.assertEquals(tasks.context_message.delay(), True)
        # Mock out mytardis api
        httpretty.enable()  # enable HTTPretty so that it will monkey patch the socket module
        httpretty.register_uri(httpretty.POST,
                               "http://acme.com/api/v1/experiment/?format=json",
                               body='{"success":"true"}',
                               content_type='text/json',  adding_headers={
                               'location': "/api/v1/experiment/42/"
                               })

        # Execute configure stage and check pre/post conditions

        def check_pre_configure(task_run_settings):
            logger.debug("check_pre_configure")
            return True

        def check_post_configure(task_run_settings):
            logger.debug("check_post_configure")
            return True

        self._execute_stages(run_context.id,
                             {'configure': (check_pre_configure,
                                            check_post_configure)})

        # Execute create stage and check pre/post conditions

        def check_pre_create(task_run_settings):
            logger.debug("check_pre_create")
            return True

        def check_post_create(task_run_settings):

            logger.debug("check_post_create")
            logger.debug("task_run_settings=%s" % task_run_settings)
            created_nodes = getval(task_run_settings,
                                   self.SCHEMA_PREFIX
                                   + "/stages/create/created_nodes")
            return str(created_nodes) == str(self.CREATED_NODES)

        # Execute create stage and check pre/post conditions
        self._execute_stages(run_context.id,
                             {'create': (check_pre_create,
                                         check_post_create)})

        def check_pre_bootstrap1(task_run_settings):
            logger.debug("check_pre_bootstrap1")
            return True

        def check_post_bootstrap1(task_run_settings):

            logger.debug("check_post_bootstrap1")
            logger.debug("task_run_settings=%s" % task_run_settings)
            bootstrapped_nodes = getval(task_run_settings,
                                   self.SCHEMA_PREFIX
                                   + "/stages/bootstrap/bootstrapped_nodes")
            logger.debug("bootstrapped_nodes=%s" % bootstrapped_nodes)
            return bootstrapped_nodes == '[]'

        # Execute bootstrap stage and check pre/post conditions

        self._execute_stages(run_context.id,
                             {'bootstrap': (check_pre_bootstrap1,
                                         check_post_bootstrap1)})

        def check_pre_bootstrap2(task_run_settings):
            logger.debug("check_pre_bootstrap2")
            logger.debug("task_run_settings=%s" % task_run_settings)
            bootstrapped_nodes = getval(task_run_settings,
                                   self.SCHEMA_PREFIX
                                   + "/stages/bootstrap/bootstrapped_nodes")
            return bootstrapped_nodes == '[]'

        def check_post_bootstrap2(task_run_settings):

            logger.debug("check_post_bootstrap2")
            logger.debug("task_run_settings=%s" % task_run_settings)
            bootstrapped_nodes = getval(task_run_settings,
                                   self.SCHEMA_PREFIX
                                   + "/stages/bootstrap/bootstrapped_nodes")
            return str(bootstrapped_nodes) == str(self.BOOTSTRAPPED_NODES)

            # Execute bootstrap stage and check pre/post conditions

        self._execute_stages(run_context.id,
                             {'bootstrap': (check_pre_bootstrap2,
                                         check_post_bootstrap2)})

        httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
        httpretty.reset()    # reset HTTPretty state (clean up registered urls and request history)
