# Copyright (C) 2013, RMIT University

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
# IN THE SOFTWARE

import os
import base64
import urllib2
import logging
import logging.config
from flexmock import flexmock
from tempfile import mkstemp
from string import lower
import json
from pprint import pformat


from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.template import Context, Template
from django.contrib.auth.models import User, Group, Permission
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from storages.backends.sftpstorage import SFTPStorage

from chiminey.smartconnectorscheduler import views
from chiminey.smartconnectorscheduler import mc
from chiminey.smartconnectorscheduler import getresults
from chiminey.smartconnectorscheduler.errors import InvalidInputError
from chiminey.smartconnectorscheduler import models
from chiminey.smartconnectorscheduler import managejobs
from chiminey.smartconnectorscheduler import tasks


logger = logging.getLogger(__name__)


class NCIStorage(SFTPStorage):

    def __init__(self, settings=None):

       # normally, settings come from settings.py file, but this class allow use of
       # parameter, which is needed if

        super(NCIStorage, self).__init__()
        if 'params' in settings:
            super(NCIStorage, self).__dict__["_params"] = settings['params']
        if 'root' in settings:
            super(NCIStorage, self).__dict__["_root_path"] = settings['root']
        if 'host' in settings:
            super(NCIStorage, self).__dict__["_host"] = settings['host']
        print super(NCIStorage, self)


class SmartConnectorSchedulerTest(TestCase):
    def setUp(self):
        self.index_url = '/index/'
        self.client = Client()
        self.experiment_id = '1'
        self.group_id = "TEST_ID000000"
        self.number_of_cores = '1'
        self.input_parameters = {'experiment_id': self.experiment_id}
        self.input_parameters['group_id'] = self.group_id
        self.input_parameters['number_of_cores'] = self.number_of_cores

    # Testing Create Stage
    def test_index_create(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        print response.content

        current_stage = 'Create'
        self.input_parameters['corestages'] = [current_stage]
        create_parameters = [lower(current_stage), '-v', self.number_of_cores]
        message = "Your group ID is %s" % self.group_id

        flexmock(mc).should_receive('start')\
        .with_args(create_parameters)\
        .and_return(self.group_id)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)

    # Testing Setup Stage
    def test_index_setup(self):
        current_stage = 'Setup'
        self.input_parameters['corestages'] = [current_stage]
        setup_parameters = [lower(current_stage), '-g', self.group_id]
        message = "Setup stage completed"

        flexmock(mc).should_receive('start')\
        .with_args(setup_parameters)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)

    # Testing Run Stage
    def test_run(self):
        settings.BDP_INPUT_DIR_PATH = '/tmp/data/input'
        settings.BDP_OUTPUT_DIR_PATH = '/tmp/data/output'

        os.system('rm -rf %s' % settings.BDP_INPUT_DIR_PATH)
        os.system('mkdir -p %s' % settings.BDP_INPUT_DIR_PATH)

        temp_file = mkstemp()
        file_name = temp_file[1]
        input_file_basename = 'test_input.txt'
        input_file_name = '%s/%s' % (settings.BDP_INPUT_DIR_PATH,
                                     input_file_basename)
        os.system('mv %s %s ' % (file_name, input_file_name))
        file = open(input_file_name, "w")
        file.write("This is an input file...")
        file.close()
        zipped_file = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
        os.system("cd %s; zip %s %s" % (settings.BDP_INPUT_DIR_PATH,
                                        zipped_file, input_file_basename))
        file = open(zipped_file, "rb")
        b64_encoded = base64.b64encode(file.read())
        file.close()

        output_dir = '%s/%s/output' % (settings.BDP_OUTPUT_DIR_PATH,
                                       self.group_id)

        print 'output %s %s' % (output_dir, os.path.exists(output_dir))
        output_file = 'output.txt'
        command = 'rm -rf %s; mkdir -p %s; cd %s;'\
                  'mkdir output_1; cd output_1;'\
                  'echo "Computation completed" > %s'\
                  % (output_dir, output_dir, output_dir, output_file)
        os.system(command)

        zipped_input_dir = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
        extracted_input_dir = '%s/%s' % (settings.BDP_INPUT_DIR_PATH,
                                         self.group_id)
        unzip_inputdir_cmd = 'unzip -o -d %s %s' % (extracted_input_dir,
                                                     zipped_input_dir)

        flexmock(os).should_receive('system').with_args(unzip_inputdir_cmd)\
        .and_return(os.system(unzip_inputdir_cmd))

        rm_outputdir_cmd = 'rm -rf %s ' % output_dir
        flexmock(os).should_receive('system').with_args(rm_outputdir_cmd)

        fake_request = flexmock(request=lambda: 'requested')
        fake_response = flexmock(read=lambda: 'responded')
        flexmock(urllib2).should_receive('Request')\
        .and_return(fake_request)
        flexmock(urllib2).should_receive('urlopen')\
        .and_return(fake_response)
        flexmock(getresults).should_receive('get_results')\
        .with_args(self.experiment_id, self.group_id, output_dir)\
        .and_return(True)

        current_stage = 'Run'
        self.input_parameters['corestages'] = [current_stage]
        self.input_parameters['input_dir'] = b64_encoded
        message = "Run stage completed. Results are ready"

        flexmock(mc).should_receive('start')\
        .and_return('COMPLETED')

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)

    # Testing Terminate Stage
    def test_index_terminate(self):
        current_stage = 'Terminate'
        self.input_parameters['corestages'] = [current_stage]
        terminate_parameters = ['teardown', '-g', self.group_id, 'yes']
        message = "Terminate stage completed"

        flexmock(mc).should_receive('start')\
        .with_args(terminate_parameters)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)


# from django import template

# def do_current_time(parser, token):
#     try:
#         # split_contents() knows not to split quoted strings.
#         tag_name, format_string = token.split_contents()
#     except ValueError:
#         raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
#     if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
#         raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
#     return CurrentTimeNode(format_string[1:-1])

# from django import template
# import datetime
# class CurrentTimeNode(template.Node):
#     def __init__(self, format_string):
#         self.format_string = format_string
#     def render(self, context):
#         return datetime.datetime.now().strftime(self.format_string)

# from django import template
# import datetime
# class CurrentTimeNode(template.Node):
#     def __init__(self, format_string):
#         self.format_string = format_string
#     def render(self, context):
#         return datetime.datetime.now().strftime(self.format_string)


class TestCommandContextLoop(TestCase):
    """
    Tests ability to translate directives with arguments
    into equivalent commands with correct template instantiated
    files and parameter type arguments and execute them.
    """

    def setUp(self):
        self.remote_fs_path = os.path.join(
            os.path.dirname(__file__), '..', 'testing', 'remotesys/').decode("utf8")
        logger.debug("self.remote_fs_path=%s" % self.remote_fs_path)
        self.remote_fs = FileSystemStorage(location=self.remote_fs_path)

    def tearDown(self):
        files = self._get_paths("")
        logger.debug("files=%s", '\n'.join(files))
        # NB: directories are not deletable using remote_fs api
        for f in files:
            pass
            self.remote_fs.delete(f)
            self.assertFalse(self.remote_fs.exists(f))

    def _get_paths(self, dir):
        (dir_list, file_list) = self.remote_fs.listdir(path=dir)
        #logger.debug("file_list from %s=%s" % (dir, file_list))
        dirs = []

        for item in dir_list:
            #logger.debug("Directory %s" % str(item))
            p = self._get_paths(os.path.join(dir, item))
            for x in p:
                #logger.debug("Inside Directory %s" % x)
                dirs.append(x)
            #dirs.append(os.path.join(dir, item))

        for item in file_list:
            #logger.debug("Item %s" % str(item))
            dirs.append(os.path.join(dir, item))

        return dirs

    # def test_event_process_loop(self):
    #     """
    #     Tests converting directive with arguments into equivalent
    #     Composite stage command and executes it in event loop
    #     """
    #     # Create a user and profile
    #     self.user = User.objects.create_user(username="username1",
    #         password="password")
    #     profile = models.UserProfile(
    #                   user=self.user)
    #     profile.save()
    #     schema_data = {
    #         u'http://rmit.edu.au/schemas//files':
    #             [u'general input files for directive',
    #             {
    #             u'file0': (models.ParameterName.STRING,''),
    #             u'file1': (models.ParameterName.STRING,''),
    #             u'file2': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #          # Note that file schema ns must match regex
    #          # protocol://host/schemas/{directective.name}/files
    #          # otherwise files will not be matched correctly.
    #          # TODO: make fall back to directive files in case specfici
    #          # version not defined here.
    #         u'http://rmit.edu.au/schemas/smartconnector1/files':
    #              [u'the smartconnector1 input files',
    #              {
    #              u'file0': (models.ParameterName.STRING,''),
    #              u'file1': (models.ParameterName.STRING,''),
    #              u'file2': (models.ParameterName.STRING,''),
    #              }
    #              ],
    #         u'http://rmit.edu.au/schemas/smartconnector_hrmc/files':
    #              [u'the smartconnector hrmc input files',
    #              {
    #              }
    #              ],
    #         u'http://rmit.edu.au/schemas/smartconnector1/create':
    #             [u'the smartconnector1 create stage config',
    #             {
    #             u'iseed': (models.ParameterName.NUMERIC,''),
    #             u'num_nodes': (models.ParameterName.NUMERIC,''),
    #             u'null_number': (models.ParameterName.NUMERIC,''),
    #             u'parallel_number': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         # we might want to reuse schemas in muliple contextsets
    #         # hence we could merge next too corestages, for example.
    #         # However, current ContextParameterSets are unamed in the
    #         # URI so we can't identify which one to use.
    #         u'http://rmit.edu.au/schemas/stages/null/testing':
    #             [u'the null stage internal testing',
    #             {
    #             u'output': (models.ParameterName.NUMERIC,''),
    #             u'index': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/parallel/testing':
    #             [u'the parallel stage internal testing',
    #             {

    #             u'output': (models.ParameterName.NUMERIC,''),
    #             u'index': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://nci.org.au/schemas/smartconnector1/custom':
    #             [u'the smartconnector1 custom command',
    #             {
    #             u'command': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/system/misc':
    #             [u'system level misc values',
    #             {
    #             u'transitions': (models.ParameterName.STRING,''),  # deprecated
    #             u'system': (models.ParameterName.STRING,''),
    #             u'id': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/system':
    #             [u'Information about the deployment platform',
    #             {
    #             u'platform': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://tardis.edu.au/schemas/hrmc/dfmeta':
    #             ["datafile",
    #             {
    #             u"a": (models.ParameterName.NUMERIC,''),
    #             u'b': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://tardis.edu.au/schemas/hrmc/dfmeta2':
    #             ["datafile2",
    #             {
    #             u'c': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         models.UserProfile.PROFILE_SCHEMA_NS:
    #             [u'user profile',
    #             {
    #                 u'userinfo1': (models.ParameterName.STRING,'test parameter1'),
    #                 u'userinfo2': (models.ParameterName.NUMERIC,'test parameter2'),
    #                 u'nci_private_key': (models.ParameterName.STRING,'location of NCI private key'),
    #                 u'nci_user': (models.ParameterName.STRING,'username for NCI access'),
    #                 u'nci_password': (models.ParameterName.STRING,'password for NCI access'),
    #                 u'nci_host': (models.ParameterName.STRING,'hostname for NCI'),
    #                 u'flag': (models.ParameterName.NUMERIC,'not used?'),
    #                 u'nectar_private_key_name': (models.ParameterName.STRING,'name of the key for nectar'),
    #                 u'nectar_private_key': (models.ParameterName.STRING,'location of NeCTAR private key'),
    #                 u'nectar_ec2_access_key': (models.ParameterName.STRING,'NeCTAR EC2 Access Key'),
    #                 u'nectar_ec2_secret_key': (models.ParameterName.STRING,'NeCTAR EC2 Secret Key'),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/copy/files':
    #              [u'the copy input files',
    #              {
    #              u'file0': (models.ParameterName.STRING,''),
    #              u'file1': (models.ParameterName.STRING,''),
    #              }
    #              ],
    #         u'http://rmit.edu.au/schemas/program/files':
    #              [u'the copy input files',
    #              {
    #              u'file0': (models.ParameterName.STRING,''),
    #              u'file1': (models.ParameterName.STRING,''),
    #              u'file2': (models.ParameterName.STRING,''),
    #              }
    #              ],
    #         u'http://rmit.edu.au/schemas/stages/copy/testing':
    #             [u'the copy stage internal testing',
    #             {
    #             u'output': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/program/testing':
    #             [u'the program stage internal testing',
    #             {
    #             u'output': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/program/config':
    #             [u'the program command internal config',
    #             {
    #             u'program': (models.ParameterName.STRING,''),
    #             u'remotehost': (models.ParameterName.STRING,''),
    #             u'program_success': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/greeting/salutation':
    #             [u'salute',
    #             {
    #             u'salutation': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/hrmc':
    #             [u'the hrmc smart connector input values',
    #             {
    #             u'number_vm_instances': (models.ParameterName.NUMERIC,''),
    #             u'iseed': (models.ParameterName.NUMERIC,''),
    #             u'input_location': (models.ParameterName.STRING,''),
    #             u'optimisation_scheme': (models.ParameterName.NUMERIC,''),
    #             u'threshold': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/configure':
    #             [u'the configure state of the hrmc smart connector',
    #             {
    #             u'configure_done': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/create':
    #             [u'the create state of the smartconnector1',
    #             {
    #             u'group_id': (models.ParameterName.STRING,''),
    #             u'vm_size': (models.ParameterName.STRING,''),
    #             u'vm_image': (models.ParameterName.STRING,''),
    #             u'security_group': (models.ParameterName.STRLIST,''),
    #             u'group_id_dir': (models.ParameterName.STRING,''),
    #             u'cloud_sleep_interval': (models.ParameterName.NUMERIC,''),
    #             u'custom_prompt': (models.ParameterName.STRING,''),
    #             u'nectar_username': (models.ParameterName.STRING, 'name of username for accessing nectar'),
    #             u'nectar_password': (models.ParameterName.STRING, 'password of username for accessing nectar'),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/setup':
    #             [u'the create stage of the smartconnector1',
    #             {
    #             u'setup_finished': (models.ParameterName.NUMERIC,''),
    #             u'payload_source': (models.ParameterName.STRING,''),
    #             u'payload_destination': (models.ParameterName.STRING,''),
    #             }
    #             ],
    #         u'http://rmit.edu.au/schemas/stages/run':
    #             [u'the create stage of the smartconnector1',
    #             {
    #             u'runs_left': (models.ParameterName.NUMERIC,''),
    #             u'max_seed_int': (models.ParameterName.NUMERIC,''),
    #             u'payload_cloud_dirname': (models.ParameterName.STRING,''),
    #             u'compile_file': (models.ParameterName.STRING,''),
    #             u'retry_attempts': (models.ParameterName.NUMERIC,''),
    #             }
    #             ],
    #     }
    #     from urlparse import urlparse
    #     from django.template.defaultfilters import slugify

    #     for ns in schema_data:
    #         l = schema_data[ns]
    #         logger.debug("l=%s" % l)
    #         desc = l[0]
    #         logger.debug("desc=%s" % desc)
    #         kv = l[1:][0]
    #         logger.debug("kv=%s", kv)

    #         url = urlparse(ns)

    #         context_schema, _ = models.Schema.objects.get_or_create(
    #             namespace=ns, defaults={'name': slugify(url.path), 'description': desc})

    #         for k, v in kv.items():
    #             val, help_text = (v[0], v[1])
    #             models.ParameterName.objects.get_or_create(schema=context_schema,
    #                 name=k, defaults={'type': val, 'help_text': help_text})


    #     self.PARAMS = {
    #             'userinfo1': 'param1val',
    #             'userinfo2': 42,
    #             'nci_user': 'root',
    #             'nci_password': 'dtofaam',  # NB: change this password
    #             'nci_host': '127.0.0.1',
    #             'nci_private_key': '',
    #             'nectar_private_key_name': '',
    #             'nectar_private_key': '',
    #             'nectar_ec2_access_key': '',
    #             'nectar_ec2_secret_key': '',
    #             }



    #     self.PARAMTYPE = {}
    #     sch = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)
    #     #paramtype = schema_data['http://www.rmit.edu.au/user/profile/1'][1]
    #     param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
    #         schema=sch)
    #     for k, v in self.PARAMS.items():
    #         param_name = models.ParameterName.objects.get(schema=sch,
    #             name=k)
    #         models.UserProfileParameter.objects.create(name=param_name,
    #             paramset=param_set,
    #             value=v)

    #     # make the system settings, available to initial stage and merged with run_settings
    #     system_dict = {u'system': u'settings'}
    #     system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}



    #     local_filesys_rootpath = '/opt/cloudenabling/current/chiminey/smartconnectorscheduler/testing/remotesys'
    #     models.Platform.objects.get_or_create(name='local', root_path=local_filesys_rootpath)
    #     models.Platform.objects.get_or_create(name='nectar', root_path='/home/centos')
    #     platform, _  = models.Platform.objects.get_or_create(name='nci', root_path=local_filesys_rootpath)

    #     # Name our smart connector directive
    #     directive = models.Directive(name="smartconnector1")
    #     directive.save()

    #     self.null_package = "chiminey.smartconnectorscheduler.corestages.nullstage.NullStage"
    #     self.parallel_package = "chiminey.smartconnectorscheduler.corestages.composite.ParallelStage"
    #     # Define all the corestages that will make up the command.  This structure
    #     # has two layers of composition
    #     composite_stage = models.Stage.objects.create(name="basic_connector",
    #          description="encapsulates a workflow",
    #          package=self.parallel_package,
    #          order=100)
    #     setup_stage = models.Stage.objects.create(name="setup",
    #         parent=composite_stage,
    #         description="This is a setup stage of something",
    #         package=self.null_package,
    #         order=0)

    #     # stage settings are usable from subsequent corestages in a run so only
    #     # need to define once for first null or parallel stage
    #     setup_stage.update_settings(
    #         {
    #         u'http://rmit.edu.au/schemas/smartconnector1/create':
    #             {
    #                 u'null_number': 4,
    #             }
    #         })

    #     stage2 = models.Stage.objects.create(name="run",
    #         parent=composite_stage,
    #         description="This is the running connector",
    #         package=self.parallel_package,
    #         order=1)

    #     stage2.update_settings(
    #         {
    #         u'http://rmit.edu.au/schemas/smartconnector1/create':
    #             {
    #                 u'parallel_number': 2
    #             }
    #         })

    #     models.Stage.objects.create(name="run1",
    #         parent=stage2,
    #         description="This is the running part 1",
    #         package=self.null_package,
    #         order=1)
    #     models.Stage.objects.create(name="run2",
    #         parent=stage2,
    #         description="This is the running part 2",
    #         package=self.null_package,
    #         order=2)
    #     models.Stage.objects.create(name="finished",
    #         parent=composite_stage,
    #         description="And here we finish everything off",
    #         package=self.null_package,
    #         order=3)
    #     logger.debug("corestages=%s" % models.Stage.objects.all())
    #     # NB: We could remote command and have direcives map directly to corestages
    #     # except that we still have to store platform somewhere and then every stage
    #     # (including those "hidden" inside composites have extra foreign key).
    #     comm = models.Command(platform=platform, directive=directive, stage=composite_stage)
    #     comm.save()

    #     # done setup

    #     logger.debug("remote_fs_path=%s" % self.remote_fs_path)

    #     # setup the required initial files
    #     self.remote_fs.save("input/input.txt",
    #      ContentFile("a={{a}} b={{b}} c={{c}}"))

    #     self.remote_fs.save("input/file.txt",
    #      ContentFile("foobar"))

    #     # directive_args would come from the external API (from mytardis)
    #         # Here is our example directive arguments

    #     directives = []
    #     directive_name = "smartconnector1"
    #     directive_args = []
    #     # Template from mytardis with corresponding metdata brought across
    #     directive_args.append(['tardis://iant@tardis.edu.au/datafile/15', []])
    #     # Template on remote storage with corresponding multiple parameter sets
    #     directive_args.append(['ssh://nci@127.0.0.1/input/input.txt',
    #         ['http://tardis.edu.au/schemas/hrmc/dfmeta', ('a', 3), ('b', 4)],
    #         ['http://tardis.edu.au/schemas/hrmc/dfmeta', ('a', 1), ('b', 2)],
    #         ['http://tardis.edu.au/schemas/hrmc/dfmeta2', ('c', 'hello')]])
    #     # A file (template with no variables)
    #     directive_args.append(['ssh://nci@127.0.0.1/input/file.txt',
    #         []])
    #     # A set of commands
    #     directive_args.append(['', ['http://rmit.edu.au/schemas/smartconnector1/create',
    #         (u'num_nodes', 5), (u'iseed', 42)]])
    #     # An Example of how a nci script might work.
    #     directive_args.append(['',
    #         ['http://nci.org.au/schemas/smartconnector1/custom', ('command', 'ls')]])

    #     platform = "nci"
    #     directives.append((platform, directive_name, directive_args))

    #     test_final_run_settings = []
    #     test_initial_run_settings = []
    #     for (platform, directive_name, directive_args) in directives:
    #         logger.debug("directive_name=%s" % directive_name)
    #         logger.debug("directive_args=%s" % directive_args)

    #         (run_settings, command_args, new_run_context) = hrmcstages.make_runcontext_for_directive(
    #             platform,
    #             directive_name,
    #             directive_args, system_settings, self.user.username)
    #         test_initial_run_settings.append((directive_name, run_settings))

    #         #test_final_run_settings.append(hrmcstages.process_all_contexts())

    #         res = []
    #         while True:
    #             contexts = models.Context.objects.filter(deleted=False)
    #             if not len(contexts):
    #                 break
    #             r = tasks.progress_context(contexts[0].id)
    #             if r:
    #                 res.append(r)

    #         test_final_run_settings.append(res)

    #     self.assertEquals(test_initial_run_settings[0][0], 'smartconnector1')

    #     self.assertEquals(sorted(test_initial_run_settings[0][1].keys()),
    #         sorted([u'http://nci.org.au/schemas/smartconnector1/custom',
    #             u'http://rmit.edu.au/schemas/smartconnector1/create',
    #             u'http://rmit.edu.au/schemas/smartconnector1/files',
    #             u'http://rmit.edu.au/schemas/system',
    #             u'http://rmit.edu.au/schemas/system/misc']))
    #     # TODO: testing values() is difficult as they files have random strings

    #     logger.debug("test_final_run_settings = %s" % pformat(test_final_run_settings))
    #     logger.debug("test_final_run_settings[0][0] = %s" % pformat(test_final_run_settings[0][0]))
    #     logger.debug("test_final_run_settings[0][0] = %s" % pformat(test_final_run_settings[0][0].keys()))

    #     self.assertEquals(test_final_run_settings[0][0][u'http://rmit.edu.au/schemas/stages/null/testing']['output'], 4)
    #     self.assertEquals(test_final_run_settings[0][0][u'http://rmit.edu.au/schemas/stages/parallel/testing']['output'], 2)
    #     logger.debug("context =  %s" % test_final_run_settings[0][0])

    def setup_envion(self):

        # Create a user and profile
        self.user = User.objects.create_user(username="username1",
            password="password")
        profile = models.UserProfile(
                      user=self.user)
        profile.save()

        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(
                codename="change_%s" % model_name)
            #delete_model = Permission.objects.get(codename="delete_%s" % model_name)
            #self.group.permissions.add(add_model)
            self.group.permissions.add(change_model)
            #self.group.permissions.add(delete_model)

        schema_data = {
            u'http://rmit.edu.au/schemas//files':
                [u'general input files for directive',
                {
                u'file0': (models.ParameterName.STRING, '', 3),
                u'file1': (models.ParameterName.STRING, '', 2),
                u'file2': (models.ParameterName.STRING, '', 1),
                }
                ],
             # Note that file schema ns must match regex
             # protocol://host/schemas/{directective.name}/files
             # otherwise files will not be matched correctly.
             # TODO: make fall back to directive files in case specfici
             # version not defined here.
            u'http://rmit.edu.au/schemas/smartconnector1/files':
                 [u'the smartconnector1 input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 3),
                 u'file1': (models.ParameterName.STRING, '', 2),
                 u'file2': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/smartconnector_hrmc/files':
                 [u'the smartconnector hrmc input files',
                 {
                 }
                 ],
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                [u'the smartconnector1 create stage config',
                {
                u'iseed': (models.ParameterName.NUMERIC, '', 4),
                u'num_nodes': (models.ParameterName.NUMERIC, '', 3),
                u'null_number': (models.ParameterName.NUMERIC, '', 2),
                u'parallel_number': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            # we might want to reuse schemas in muliple contextsets
            # hence we could merge next too corestages, for example.
            # However, current ContextParameterSets are unamed in the
            # URI so we can't identify which one to use.
            u'http://rmit.edu.au/schemas/stages/null/testing':
                [u'the null stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 2),
                u'index': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/parallel/testing':
                [u'the parallel stage internal testing',
                {

                u'output': (models.ParameterName.NUMERIC, '', 2),
                u'index': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://nci.org.au/schemas/smartconnector1/custom':
                [u'the smartconnector1 custom command',
                {
                u'command': (models.ParameterName.STRING, '', 2),
                }
                ],
            u'http://rmit.edu.au/schemas/system/misc':
                [u'system level misc values',
                {
                u'transitions': (models.ParameterName.STRING, '', 4),  # deprecated
                u'system': (models.ParameterName.STRING, '', 3),
                u'id': (models.ParameterName.NUMERIC, '', 2),
                }
                ],
            u'http://rmit.edu.au/schemas/system':
                [u'Information about the deployment platform',
                {
                u'platform': (models.ParameterName.STRING, '', 2),
                u'contextid': (models.ParameterName.NUMERIC, '', 1)
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta':
                ["datafile",
                {
                u"a": (models.ParameterName.NUMERIC, '', 2),
                u'b': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta2':
                ["datafile2",
                {
                u'c': (models.ParameterName.STRING, '', 1),
                }
                ],
            models.UserProfile.PROFILE_SCHEMA_NS:
                [u'user profile',
                {
                    u'userinfo1': (models.ParameterName.STRING,
                        'test parameter1', 11),
                    u'userinfo2': (models.ParameterName.NUMERIC,
                        'test parameter2', 10),
                    u'nci_private_key': (models.ParameterName.STRING,
                        'location of NCI private key', 9),
                    u'nci_user': (models.ParameterName.STRING,
                        'username for NCI access', 8),
                    u'nci_password': (models.ParameterName.STRING,
                        'password for NCI access', 7),
                    u'nci_host': (models.ParameterName.STRING,
                        'hostname for NCI', 6),
                    u'flag': (models.ParameterName.NUMERIC,
                        'not used?', 5),
                    u'nectar_private_key_name': (models.ParameterName.STRING,
                        'name of the key for nectar', 4),
                    u'nectar_private_key': (models.ParameterName.STRING,
                        'location of NeCTAR private key', 3),
                    u'nectar_ec2_access_key': (models.ParameterName.STRING,
                        'NeCTAR EC2 Access Key', 2),
                    u'nectar_ec2_secret_key': (models.ParameterName.STRING,
                        'NeCTAR EC2 Secret Key', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/copy/files':
                 [u'the copy input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 2),
                 u'file1': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/program/files':
                 [u'the copy input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 3),
                 u'file1': (models.ParameterName.STRING, '', 2),
                 u'file2': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/stages/copy/testing':
                [u'the copy stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/program/testing':
                [u'the program stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/program/config':
                [u'the program command internal config',
                {
                u'program': (models.ParameterName.STRING, '', 3),
                u'remotehost': (models.ParameterName.STRING, '', 2),
                u'program_success': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/greeting/salutation':
                [u'salute',
                {
                u'salutation': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/hrmc':
                [u'the hrmc smart connector input values',
                {
                u'number_vm_instances': (models.ParameterName.NUMERIC, '', 7),
                u'iseed': (models.ParameterName.NUMERIC, '', 6),
                u'input_location': (models.ParameterName.STRING, '', 5),
                u'optimisation_scheme': (models.ParameterName.STRLIST, '', 4),
                u'threshold': (models.ParameterName.STRING, '', 3),  # FIXME: should be list of ints
                u'error_threshold': (models.ParameterName.STRING, '', 2),  # FIXME: should use float here
                u'max_iteration': (models.ParameterName.NUMERIC, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/configure':
                [u'the configure state of the hrmc smart connector',
                {
                u'configure_done': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/create':
                [u'the create state of the smartconnector1',
                {
                u'group_id': (models.ParameterName.STRING, '', 9),
                u'vm_size': (models.ParameterName.STRING, '', 8),
                u'vm_image': (models.ParameterName.STRING, '', 7),
                u'security_group': (models.ParameterName.STRLIST, '', 6),
                u'group_id_dir': (models.ParameterName.STRING, '', 5),
                u'cloud_sleep_interval': (models.ParameterName.NUMERIC, '', 4),
                u'custom_prompt': (models.ParameterName.STRING, '', 3),
                u'nectar_username': (models.ParameterName.STRING,
                    'name of username for accessing nectar', 2),
                u'nectar_password': (models.ParameterName.STRING,
                    'password of username for accessing nectar', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/setup':
                [u'the create stage of the smartconnector1',
                {
                u'setup_finished': (models.ParameterName.NUMERIC, '', 3),
                u'payload_source': (models.ParameterName.STRING, '', 2),
                u'payload_destination': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/deploy':
                [u'the deploy stage of the smartconnector1',
                {
                u'started': (models.ParameterName.STRING, '', 2),
                u'deployed_nodes': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/run':
                [u'the create stage of the smartconnector1',
                {
                u'runs_left': (models.ParameterName.NUMERIC, '', 10),
                u'max_seed_int': (models.ParameterName.NUMERIC, '', 9),
                u'payload_cloud_dirname': (models.ParameterName.STRING, '', 8),
                u'compile_file': (models.ParameterName.STRING, '', 7),
                u'retry_attempts': (models.ParameterName.NUMERIC, '', 6),
                u'error_nodes': (models.ParameterName.NUMERIC, '', 5),
                u'initial_numbfile': (models.ParameterName.NUMERIC, '', 4),
                u'random_numbers': (models.ParameterName.STRING, '', 3),
                u'rand_index': (models.ParameterName.NUMERIC, '', 2),
                u'finished_nodes': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/transform':
                [u'the transform stage of the smartconnector1',
                {
                u'transformed': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/converge':
                [u'the converge stage of the smartconnector1',
                {
                u'converged': (models.ParameterName.STRING, '', 2),  # FIXME: use NUMERIC for booleans (with 0,1)
                u'criterion': (models.ParameterName.STRING, '', 1),  # Use STRING as float not implemented
                }
                ],
            u'http://rmit.edu.au/schemas/stages/teardown':
                [u'the teardown stage of the smartconnector1',
                {
                u'run_finished': (models.ParameterName.STRING, '', 1),  # FIXME: use NUMERIC for booleans (with 0,1)
                }
                ],

        }

        from urlparse import urlparse
        from django.template.defaultfilters import slugify

        for ns in schema_data:
            l = schema_data[ns]
            logger.debug("l=%s" % l)
            desc = l[0]
            logger.debug("desc=%s" % desc)
            kv = l[1:][0]
            logger.debug("kv=%s", kv)

            url = urlparse(ns)

            context_schema, _ = models.Schema.objects.get_or_create(
                namespace=ns,
                defaults={'name': slugify(url.path.replace('/', ' ')),
                    'description': desc})

            for k, v in kv.items():
                val, help_text, ranking = (v[0], v[1], v[2])
                models.ParameterName.objects.get_or_create(
                    schema=context_schema,
                    name=k,
                    defaults={
                        'type': val, 'help_text': help_text,
                        'ranking': ranking})

        self.PARAMS = {
            'userinfo1': 'param1val',
            'userinfo2': 42,
            'nci_user': 'root',
            'nci_password': 'dtofaamdtofaam',  # NB: change this password
            'nci_host': '127.0.0.1',
            'nci_private_key': '',
            'nectar_private_key': 'file://local@127.0.0.1/mynectarkey.pem',
            'nectar_private_key_name': '',
            'nectar_ec2_access_key': '',
            'nectar_ec2_secret_key': '',
            }

        self.PARAMTYPE = {}
        sch = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)
        #paramtype = schema_data['http://www.rmit.edu.au/user/profile/1'][1]
        param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
            schema=sch)
        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.get(schema=sch,
                name=k)
            models.UserProfileParameter.objects.create(name=param_name,
                paramset=param_set,
                value=v)

        local_filesys_rootpath = '/opt/cloudenabling/current/chiminey/smartconnectorscheduler/testing/remotesys'
        models.Platform.objects.get_or_create(name='local',
            root_path=local_filesys_rootpath)
        nectar_platform, _ = models.Platform.objects.get_or_create(
            name='nectar', root_path='/home/centos')
        self.platform, _ = models.Platform.objects.get_or_create(
            name='nci', root_path=local_filesys_rootpath)

    def test_multi_remote_commands(self):
        """
        Tests converting multiple directives with arguments into equivalent
        Composite stage command and executes it in event loop
        """

        self.setup_envion()

        copy_dir = models.Directive(name="copy")
        copy_dir.save()
        program_dir = models.Directive(name="program")
        program_dir.save()

        self.movement_stage = "chiminey.smartconnectorscheduler.corestages.movement.CopyFileStage"
        self.program_stage = "chiminey.smartconnectorscheduler.corestages.program.LocalProgramStage"
        # Define all the corestages that will make up the command.  This structure
        # has two layers of composition
        copy_stage = models.Stage.objects.create(name="copy",
             description="data movemement operation",
             package=self.movement_stage,
             order=100)

        #copy_stage.update_settings({
        #    u'http://rmit.edu.au/schemas/stages/copy/testing':
        #        {
        #        u'output':0
        #        }})

        program_stage = models.Stage.objects.create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)

        #program_stage.update_settings({u'http://rmit.edu.au/schemas/stages/program/testing':
        #        {
        #        u'output':0
        #        }})

        logger.debug("corestages=%s" % models.Stage.objects.all())
        # Make a new command that reliases composite_stage
        # TODO: add the command program to the model
        comm = models.Command(platform=self.platform, directive=copy_dir, stage=copy_stage)
        comm.save()
        comm = models.Command(platform=self.platform, directive=program_dir, stage=program_stage)
        comm.save()

        # We could make one command with a composite containing three corestages or
        # three commands each containing a single stage.

        # done setup

        logger.debug("remote_fs_path=%s" % self.remote_fs_path)

        self.remote_fs.save("local/greet.txt",
            ContentFile("{{salutation}} World"))

        self.remote_fs.save("remote/greetaddon.txt",
            ContentFile("(remotely)"))

        platform = "nci"

        directives = []

        # Instantiate a template locally, then copy to remote
        directive_name = "copy"
        directive_args = []
        directive_args.append(
            ['file://local@127.0.0.1/local/greet.txt',
                ['http://rmit.edu.au/schemas/greeting/salutation',
                    ('salutation', 'Hello')]])
        directive_args.append(['ssh://nci@127.0.0.1/remote/greet.txt', []])
        directives.append((platform, directive_name, directive_args))

        # concatenate that file and another file (already remote) to form result
        directive_args = []
        directive_name = "program"
        directive_args.append(['',
            ['http://rmit.edu.au/schemas/program/config', ('program', 'cat'),
            ('remotehost', '127.0.0.1')]])

        directive_args.append(['ssh://nci@127.0.0.1/remote/greet.txt',
            []])
        directive_args.append(['ssh://nci@127.0.0.1/remote/greetaddon.txt',
            []])
        directive_args.append(['ssh://nci@127.0.0.1/remote/greetresult.txt',
            []])

        directives.append((platform, directive_name, directive_args))

        # transfer result back locally.
        directive_name = "copy"
        directive_args = []
        directive_args.append(['ssh://nci@127.0.0.1/remote/greetresult.txt',
            []])
        directive_args.append(['file://local@127.0.0.1/local/finalresult.txt',
            []])

        directives.append((platform, directive_name, directive_args))

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        test_final_run_settings = []
        test_initial_run_settings = []
        for (platform, directive_name, directive_args) in directives:
            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)

            (run_settings, command_args, new_run_context) = managejobs.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.user.username)

            test_initial_run_settings.append((directive_name, run_settings))

            # do all the processing of corestages for all available contexts for all users.
            # NB: a user can have multiple run contexts, but they will be processed
            # in a undefined order. TODO: build a run_context sequence model of some kind.

            res = []
            while True:
                contexts = models.Context.objects.filter(deleted=False)
                if not len(contexts):
                    break
                r = tasks.progress_context(contexts[0].id)
                if r:
                    res.append(r)

            test_final_run_settings.append(res)

            #test_final_run_settings.append(hrmcstages.process_all_contexts())
            logger.debug("test_final_run_settings = %s" % pformat(test_final_run_settings))

        logger.debug("test_initial_run_settings = %s" % pformat(test_initial_run_settings))

        correct_initial_run_settings = [
        ('copy',
            [u'http://rmit.edu.au/schemas/copy/files',
            u'http://rmit.edu.au/schemas/system',
            u'http://rmit.edu.au/schemas/system/misc']
            ),

        ('program',
            [u'http://rmit.edu.au/schemas/program/config',
            u'http://rmit.edu.au/schemas/program/files',
            u'http://rmit.edu.au/schemas/system',
            u'http://rmit.edu.au/schemas/system/misc']
            ),
        ('copy',
            [u'http://rmit.edu.au/schemas/copy/files',
            u'http://rmit.edu.au/schemas/system',
            u'http://rmit.edu.au/schemas/system/misc']
            ),
        ]
        for test_init_run_settings, correct_init_run_settings in zip(test_initial_run_settings,
            correct_initial_run_settings):
            logger.debug("tirs=%s" % sorted(test_init_run_settings[1].keys()))
            logger.debug("cirs=%s" % sorted(correct_init_run_settings[1]))
            self.assertEquals(test_init_run_settings[0], correct_init_run_settings[0])
            self.assertEquals(sorted(test_init_run_settings[1].keys()),
                sorted(correct_init_run_settings[1]))

        logger.debug("test_info = %s" % json.dumps(test_final_run_settings, indent=4))

        test1 = test_final_run_settings[0]
        logger.debug("test1=%s" % test1)
        test2 = test_final_run_settings[1]
        logger.debug("test2=%s" % test2)
        test3 = test_final_run_settings[2]
        logger.debug("test3=%s" % test3)
        self.assertEquals(test1[0]['http://rmit.edu.au/schemas/stages/copy/testing']['output'], 1)
        self.assertEquals(test2[0]['http://rmit.edu.au/schemas/stages/program/testing']['output'], 1)
        self.assertEquals(test3[0]['http://rmit.edu.au/schemas/stages/copy/testing']['output'], 1)

        res = self.remote_fs.open("local/finalresult.txt").read()
        logger.info(res)
        self.assertEquals(res, "Hello World(remotely)")

    def test_hrmc_smart_connector(self):
        """

        """
        self.setup_envion()

        # Name our smart connector directive
        directive = models.Directive(name="smartconnector1")
        directive.save()

        self.null_package = "chiminey.smartconnectorscheduler.corestages.nullstage.NullStage"
        self.parallel_package = "chiminey.smartconnectorscheduler.corestages.composite.ParallelStage"
        # Define all the corestages that will make up the command.  This structure
        # has two layers of composition
        composite_stage = models.Stage.objects.create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)
        setup_stage = models.Stage.objects.create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)

        # stage settings are usable from subsequent corestages in a run so only
        # need to define once for first null or parallel stage
        setup_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'null_number': 4,
                }
            })

        stage2 = models.Stage.objects.create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)

        stage2.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'parallel_number': 2
                }
            })

        models.Stage.objects.create(name="run1",
            parent=stage2,
            description="This is the running part 1",
            package=self.null_package,
            order=1)
        models.Stage.objects.create(name="run2",
            parent=stage2,
            description="This is the running part 2",
            package=self.null_package,
            order=2)
        models.Stage.objects.create(name="finished",
            parent=composite_stage,
            description="And here we finish everything off",
            package=self.null_package,
            order=3)
        logger.debug("corestages=%s" % models.Stage.objects.all())
        # NB: We could remote command and have direcives map directly to corestages
        # except that we still have to store platform somewhere and then every stage
        # (including those "hidden" inside composites have extra foreign key).
        comm = models.Command(platform=self.platform, directive=directive, stage=composite_stage)
        comm.save()

        # done setup

        logger.debug("remote_fs_path=%s" % self.remote_fs_path)

        # setup the required initial files
        self.remote_fs.save("input/input.txt",
         ContentFile("a={{a}} b={{b}} c={{c}}"))

        self.remote_fs.save("input/file.txt",
         ContentFile("foobar"))

        # directive_args would come from the external API (from mytardis)
            # Here is our example directive arguments

        directives = []
        directive_name = "smartconnector1"
        directive_args = []
        # Template from mytardis with corresponding metdata brought across
        directive_args.append(['tardis://iant@tardis.edu.au/datafile/15', []])
        # Template on remote storage with corresponding multiple parameter sets
        directive_args.append(['ssh://nci@127.0.0.1/input/input.txt',
            ['http://tardis.edu.au/schemas/hrmc/dfmeta', ('a', 3), ('b', 4)],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta', ('a', 1), ('b', 2)],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta2', ('c', 'hello')]])
        # A file (template with no variables)
        directive_args.append(['ssh://nci@127.0.0.1/input/file.txt',
            []])
        # A set of commands
        directive_args.append(['', ['http://rmit.edu.au/schemas/smartconnector1/create',
            (u'num_nodes', 5), (u'iseed', 42)]])
        # An Example of how a nci script might work.
        directive_args.append(['',
            ['http://nci.org.au/schemas/smartconnector1/custom', ('command', 'ls')]])

        platform = "nci"
        directives.append((platform, directive_name, directive_args))

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        test_final_run_settings = []
        test_initial_run_settings = []
        for (platform, directive_name, directive_args) in directives:
            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)

            (run_settings, command_args, new_run_context) = managejobs.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.user.username)
            test_initial_run_settings.append((directive_name, run_settings))

            #test_final_run_settings.append(hrmcstages.process_all_contexts())

            res = []
            while True:
                contexts = models.Context.objects.filter(deleted=False)
                if not len(contexts):
                    break
                r = tasks.progress_context(contexts[0].id)
                if r:
                    res.append(r)

            test_final_run_settings.append(res)

        self.assertEquals(test_initial_run_settings[0][0], 'smartconnector1')

        self.assertEquals(sorted(test_initial_run_settings[0][1].keys()),
            sorted([u'http://nci.org.au/schemas/smartconnector1/custom',
                u'http://rmit.edu.au/schemas/smartconnector1/create',
                u'http://rmit.edu.au/schemas/smartconnector1/files',
                u'http://rmit.edu.au/schemas/system',
                u'http://rmit.edu.au/schemas/system/misc']))
        # TODO: testing values() is difficult as they files have random strings

        logger.debug("test_final_run_settings = %s" % pformat(test_final_run_settings))
        logger.debug("test_final_run_settings[0][0] = %s" % pformat(test_final_run_settings[0][0]))
        logger.debug("test_final_run_settings[0][0] = %s" % pformat(test_final_run_settings[0][0].keys()))

        self.assertEquals(test_final_run_settings[0][0][u'http://rmit.edu.au/schemas/stages/null/testing']['output'], 4)
        self.assertEquals(test_final_run_settings[0][0][u'http://rmit.edu.au/schemas/stages/parallel/testing']['output'], 2)
        logger.debug("context =  %s" % test_final_run_settings[0][0])



