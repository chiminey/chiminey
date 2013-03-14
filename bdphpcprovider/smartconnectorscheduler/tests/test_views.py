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
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from storages.backends.sftpstorage import SFTPStorage



from bdphpcprovider.smartconnectorscheduler import views
from bdphpcprovider.smartconnectorscheduler import mc
from bdphpcprovider.smartconnectorscheduler import getresults
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages


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
        self.input_parameters['stages'] = [current_stage]
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
        self.input_parameters['stages'] = [current_stage]
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
        self.input_parameters['stages'] = [current_stage]
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
        self.input_parameters['stages'] = [current_stage]
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

    def test_event_process_loop(self):
        """
        Tests converting directive with arguments into equivalent
        Composite stage command and executes it in event loop
        """
        # Create a user and profile
        self.user = User.objects.create_user(username="username1",
            password="password")
        profile = models.UserProfile(
                      user=self.user)
        profile.save()

        # Create the schemas for template parameters or config info
        # specfied in directive arguments
        for ns, name, desc in [('http://www.rmit.edu.au/user/profile/1',
            "userprofile1", "Information about user"),
            ('http://tardis.edu.au/schemas/hrmc/dfmeta/', "datafile1",
                "datafile 1 schema"),
            ('http://tardis.edu.au/schemas/hrmc/dfmeta2/', "datafile2",
                "datafile 2 schema"),
            ('http://tardis.edu.au/schemas/hrmc/create', "create",
                "create stage"),
            ("http://nci.org.au/schemas/hrmc/custom_command/", "custom",
                "custom command")
            ]:
            sch = models.Schema.objects.create(namespace=ns, name=name, description=desc)
            logger.debug("sch=%s" % sch)

        # Create the schema for stages (currently only one) and all allowed
        # values and their types for all stages.
        context_schema = models.Schema.objects.create(
            namespace=models.Context.CONTEXT_SCHEMA_NS,
            name="Context Schema", description="Schema for a context")
        # We assume that a run_context has only one schema at the moment, as
        # we have to load up this schema with all context values used in
        # any of the stages (and any parameters required for the stage
        # invocation)
        # TODO: allow multiple ContextParameterSet each with different schema
        # so each value will come from a namespace.  e.g., general/fsys
        # nectar/num_of_nodes, setup/nodes_setup etc.
        for name, param_type in {
            u'file0': models.ParameterName.STRING,
            u'file1': models.ParameterName.STRING,
            u'file2': models.ParameterName.STRING,
            u'num_nodes': models.ParameterName.NUMERIC,
            u'iseed': models.ParameterName.NUMERIC,
            u'command': models.ParameterName.STRING,
            u'transitions': models.ParameterName.STRING,  # TODO: use STRLIST
            u'null_output': models.ParameterName.NUMERIC,
            u'parallel_output': models.ParameterName.NUMERIC,
            u'system': models.ParameterName.STRING,
            u'platform': models.ParameterName.NUMERIC,
            u'program_success': models.ParameterName.STRING,
            u'null_output': models.ParameterName.NUMERIC,
            u'parallel_output': models.ParameterName.NUMERIC,
            u'null_number': models.ParameterName.NUMERIC,
            u'parallel_number': models.ParameterName.NUMERIC,
            u'null_index': models.ParameterName.NUMERIC,
            u'parallel_index': models.ParameterName.NUMERIC,
            }.items():
            models.ParameterName.objects.create(schema=context_schema,
                name=name,
                type=param_type)

        # Setup the schema for user configuration information (kept in profile)
        self.PARAMS = {'userinfo1': 'param1val',
            'userinfo2': 42,
            'fsys': self.remote_fs_path,
            'nci_user': 'root',
            'nci_password': 'password',
            'nci_host': '127.0.0.1',
            }
        self.PARAMTYPE = {'userinfo1': models.ParameterName.STRING,
            'userinfo2': models.ParameterName.NUMERIC,
            'fsys': models.ParameterName.STRING,
            'nci_user': models.ParameterName.STRING,
            'nci_password': models.ParameterName.STRING,
            'nci_host': models.ParameterName.STRING}
        param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
            schema=sch)
        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.create(schema=sch,
                name=k,
                type=self.PARAMTYPE[k])
            models.UserProfileParameter.objects.create(name=param_name,
                paramset=param_set,
                value=v)

        # make the system settings, available to initial stage and merged with run_settings
        system_settings = {u'system': u'settings'}

        # Make a platform for the commands
        platform = models.Platform(name="nci")
        platform.save()

        # Name our smart connector directive
        directive = models.Directive(name="smartconnector1")
        directive.save()

        self.null_package = "bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage"
        self.parallel_package = "bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        composite_stage = models.Stage.objects.create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)
        models.Stage.objects.create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)
        stage2 = models.Stage.objects.create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)
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
        logger.debug("stages=%s" % models.Stage.objects.all())
        # NB: We could remote command and have direcives map directly to stages
        # except that we still have to store platform somewhere and then every stage
        # (including those "hidden" inside composites have extra foreign key).
        comm = models.Command(platform=platform, directive=directive, stage=composite_stage)
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
        directive_args.append(['hpc://iant@nci.edu.au/input/input.txt',
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/', ('a', 3), ('b', 4)],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/', ('a', 1), ('b', 2)],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta2/', ('c', 'hello')]])
        # A file (template with no variables)
        directive_args.append(['hpc://iant@nci.edu.au/input/file.txt',
            []])
        # A set of commands
        directive_args.append(['', ['http://tardis.edu.au/schemas/hrmc/create',
            ('num_nodes', 5), ('iseed', 42), ('null_number', 4), ('parallel_number', 1)]])
        # An Example of how a nci script might work.
        directive_args.append(['',
            ['http://nci.org.au/schemas/hrmc/custom_command/', ('command', 'ls')]])

        platform = "nci"
        directives.append((platform, directive_name, directive_args))

        test_final_run_settings = []
        test_initial_run_settings = []
        for (platform, directive_name, directive_args) in directives:
            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)

            (run_settings, command_args, new_run_context) = hrmcstages.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.user.username)
            test_initial_run_settings.append((directive_name, run_settings))

            # do all the processing of stages for all available contexts for all users.
            test_final_run_settings.append(hrmcstages.process_all_contexts())

        self.assertEquals(test_initial_run_settings[0][0], 'smartconnector1')
        self.assertEquals(sorted(test_initial_run_settings[0][1].keys()),
            sorted(
            [u'command', u'file0', u'file1', u'file2',
            u'iseed', u'num_nodes', u'platform', u'transitions', u'system',
            u'null_number', u'parallel_number']))
        # TODO: testing values() is difficult as they files have random strings

        logger.debug("test_final_run_settings = %s" % test_final_run_settings)

        self.assertEquals(test_final_run_settings[0][0][u'null_output'], 4)
        self.assertEquals(test_final_run_settings[0][0][u'parallel_output'], 1)
        logger.debug("context =  %s" % test_final_run_settings[0][0])

    def test_multi_remote_commands(self):
        """
        Tests converting multiple directives with arguments into equivalent
        Composite stage command and executes it in event loop
        """

        # Create a user and profile
        self.user = User.objects.create_user(username="username1",
            password="password")
        profile = models.UserProfile(
                      user=self.user)
        profile.save()

        # Create the schemas for template parameters or config info
        # specfied in directive arguments
        for ns, name, desc in [('http://www.rmit.edu.au/user/profile/1',
            "userprofile1", "Information about user"),
            ('http://rmit.edu.au/schemas/greeting/salutation', "salutation",
                "The form of salutation"),
            ("http://rmit.edu.au/schemas/program", "program",
                "A remote executing program")
            ]:
            sch = models.Schema.objects.create(namespace=ns, name=name, description=desc)
            logger.debug("sch=%s" % sch)

        # Create the schema for stages (currently only one) and all allowed
        # values and their types for all stages.
        context_schema = models.Schema.objects.create(
            namespace=models.Context.CONTEXT_SCHEMA_NS,
            name="Context Schema", description="Schema for run settings")
        # We assume that a run_context has only one schema at the moment, as
        # we have to load up this schema with all run settings values used in
        # any of the stages (and any parameters required for the stage
        # invocation)
        # TODO: allow multiple ContextParameterSet each with different schema
        # so each value will come from a namespace.  e.g., general/fsys
        # nectar/num_of_nodes, setup/nodes_setup etc.
        for name, param_type in {
            u'file0': models.ParameterName.STRING,
            u'file1': models.ParameterName.STRING,
            u'file2': models.ParameterName.STRING,
            u'program': models.ParameterName.STRING,
            u'remotehost': models.ParameterName.STRING,
            u'salutation': models.ParameterName.NUMERIC,
            u'transitions': models.ParameterName.STRING,  # TODO: use STRLIST
            u'program_output': models.ParameterName.NUMERIC,
            u'movement_output': models.ParameterName.NUMERIC,
            u'platform': models.ParameterName.NUMERIC,
            u'system': models.ParameterName.STRING,
            u'program_success': models.ParameterName.STRING,
            u'null_output': models.ParameterName.NUMERIC,
            u'parallel_output': models.ParameterName.NUMERIC,
            u'null_number': models.ParameterName.NUMERIC,
            u'parallel_number': models.ParameterName.NUMERIC,
            u'null_index': models.ParameterName.NUMERIC,
            u'parallel_index': models.ParameterName.NUMERIC,
            }.items():
            models.ParameterName.objects.create(schema=context_schema,
                name=name,
                type=param_type)

        # Setup the schema for user configuration information (kept in profile)
        self.PARAMS = {'userinfo1': 'param1val',
            'fsys': self.remote_fs_path,
            'nci_user': 'root',
            'nci_password': 'password',
            'nci_host': '127.0.0.1',
            'PASSWORD': 'password',
            'USER_NAME': 'root',
            'PRIVATE_KEY': '',
            }
        self.PARAMTYPE = {'userinfo1': models.ParameterName.STRING,
            'fsys': models.ParameterName.STRING,
            'nci_user': models.ParameterName.STRING,
            'nci_password': models.ParameterName.STRING,
            'nci_host': models.ParameterName.STRING,
            'PASSWORD': models.ParameterName.STRING,
            'USER_NAME': models.ParameterName.STRING,
            'PRIVATE_KEY': models.ParameterName.STRING}
        param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
            schema=sch)
        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.create(schema=sch,
                name=k,
                type=self.PARAMTYPE[k])
            models.UserProfileParameter.objects.create(name=param_name,
                paramset=param_set,
                value=v)

        # make the system settings, available to initial stage and merged with run_settings
        system_settings = {u'system': u'settings'}

        # Make a platform for the commands
        platform = models.Platform(name="nci")
        platform.save()

        copy_dir = models.Directive(name="copy")
        copy_dir.save()
        program_dir = models.Directive(name="program")
        program_dir.save()

        self.movement_stage = "bdphpcprovider.smartconnectorscheduler.stages.movement.MovementStage"
        self.program_stage = "bdphpcprovider.smartconnectorscheduler.stages.program.ProgramStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        copy_stage = models.Stage.objects.create(name="copy",
             description="data movemement operation",
             package=self.movement_stage,
             order=100)
        program_stage = models.Stage.objects.create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)
        logger.debug("stages=%s" % models.Stage.objects.all())
        # Make a new command that reliases composite_stage
        # TODO: add the command program to the model
        comm = models.Command(platform=platform, directive=copy_dir, stage=copy_stage)
        comm.save()
        comm = models.Command(platform=platform, directive=program_dir, stage=program_stage)
        comm.save()

        # We could make one command with a composite containing three stages or
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
            ['local://12.0.0.1/local/greet.txt',
                ['http://rmit.edu.au/schemas/greeting/salutation',
                    ('salutation', 'Hello')]])
        directive_args.append(['hpc://ncitest.org/remote/greet.txt', []])
        directives.append((platform, directive_name, directive_args))

        # concatenate that file and another file (already remote) to form result
        directive_args = []
        directive_name = "program"
        directive_args.append(['',
            ['http://rmit.edu.au/schemas/program', ('program', 'cat'),
            ('remotehost', '127.0.0.1')]])

        directive_args.append(['hpc://ncitest.org/remote/greet.txt',
            []])
        directive_args.append(['hpc://ncitest.org/remote/greetaddon.txt',
            []])
        directive_args.append(['hpc://ncitest.org/remote/greetresult.txt',
            []])

        directives.append((platform, directive_name, directive_args))

        # transfer result back locally.
        directive_name = "copy"
        directive_args = []
        directive_args.append(['hpc://ncitest.org/remote/greetresult.txt',
            []])
        directive_args.append(['local://12.0.0.1/local/finalresult.txt',
            []])

        directives.append((platform, directive_name, directive_args))

        test_final_run_settings = []
        test_initial_run_settings = []
        for (platform, directive_name, directive_args) in directives:
            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)

            (run_settings, command_args, new_run_context) = hrmcstages.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.user.username)

            test_initial_run_settings.append((directive_name, run_settings))

            # do all the processing of stages for all available contexts for all users.
            # NB: a user can have multiple run contexts, but they will be processed
            # in a undefined order. TODO: build a run_context sequence model of some kind.
            test_final_run_settings.append(hrmcstages.process_all_contexts())
            logger.debug("test_final_run_settings = %s" % pformat(test_final_run_settings))

        logger.debug("test_initial_run_settings = %s" % pformat(test_initial_run_settings))

        correct_initial_run_settings = [
        ('copy', [u'file0', u'file1',
                u'platform', u'transitions', u'system']),

        ('program', [u'file0', u'file1', u'file2', u'program', u'remotehost',
            u'platform', u'transitions', u'system']),

        ('copy', [u'file0', u'file1',
                u'platform', u'transitions', u'system'])
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
        self.assertEquals(test1[0]['movement_output'], 1)
        self.assertEquals(test2[0]['program_output'], 1)
        self.assertEquals(test3[0]['movement_output'], 1)

        res = self.remote_fs.open("local/finalresult.txt").read()
        logger.info(res)
        self.assertEquals(res, "Hello World(remotely)")






