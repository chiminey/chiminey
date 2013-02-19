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
import tempfile

from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.template import Context, Template
from django.contrib.auth.models import User


from bdphpcprovider.smartconnectorscheduler import views
from bdphpcprovider.smartconnectorscheduler import mc
from bdphpcprovider.smartconnectorscheduler import getresults
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


class SmartConnectorSchedulerTest(TestCase):
    def setUp(self):
        self.index_url = '/index/'
        self.client = Client()
        self.experiment_id = '1'
        self.group_id = "TEST_ID000000"
        self.number_of_cores = '1'
        self.input_parameters = {'experiment_id' : self.experiment_id}
        self.input_parameters['group_id'] = self.group_id
        self.input_parameters['number_of_cores'] = self.number_of_cores

    # Testing Create Stage
    def test_index_create(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        print response.content

        current_stage = 'Create'
        self.input_parameters['stages'] = [current_stage]
        create_parameters= [lower(current_stage), '-v', self.number_of_cores]
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
        setup_parameters= [lower(current_stage), '-g', self.group_id]
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
                  %(output_dir, output_dir, output_dir, output_file)
        os.system(command)

        zipped_input_dir = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
        extracted_input_dir = '%s/%s' % (settings.BDP_INPUT_DIR_PATH,
                                         self.group_id)
        unzip_inputdir_cmd =  'unzip -o -d %s %s' % (extracted_input_dir,
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
        terminate_parameters=  ['teardown', '-g', self.group_id, 'yes']
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


class TestDirectiveCommands(TestCase):
    """
    Tests ability to translate directives with arguments
    into equivalent commands with correct template instantiated
    files and parameter type arguments
    """

    def setUp(self):
        pass

    def _load_data(self, params, paramtype):

        self.user = User.objects.create_user(username="username1",
            password="password")
        profile = models.UserProfile(
                      user=self.user)
        profile.save()

        for ns, name, desc in [('http://www.rmit.edu.au/user/profile/1',
            "userprofile1", "Information about user"),
            ('http://tardis.edu.au/schemas/hrmc/dfmeta/',"datafile1","datafile 1 schema"),
            ('http://tardis.edu.au/schemas/hrmc/dfmeta2/', "datafile2", "datafile 2 schema"),
            ('http://tardis.edu.au/schemas/hrmc/create', "create", "create stage" ),
            ("http://nci.org.au/schemas/hrmc/custom_command/", "custom", "custom command")
            ]:
            sch = models.Schema(namespace=ns, name=name, description=desc)
            sch.save()
            logger.debug("sch=%s" % sch)


        param_set = models.UserProfileParameterSet(user_profile=profile, schema=sch)
        param_set.save()
        for k, v in params.items():
            param_name = models.ParameterName(schema=sch, name=k, type=paramtype[k])
            param_name.save()
            param = models.UserProfileParameter(name=param_name, paramset=param_set,
                value=v)
            param.save()

        # comm = Command(platform="nci")
        # comm.save()
        
#        m = models.CommandMapping(directive=direct, command=comm)
#        m.save()

#        direct = models.Directive(name="smartconnector1",
#            command='hrmc'
#        direct.save()


    def test_simple(self):

        # setup all needed schemas below
        PARAMS = {'param1name': 'param1val',
            'param2name': '42'}
        PARAMS_RIGHTTYPES = {'param1name': 'param1val',
            'param2name': 42}
        PARAMTYPE = {'param1name': models.ParameterName.STRING,
            'param2name': models.ParameterName.NUMERIC}
        self._load_data(PARAMS, PARAMTYPE)


        # Here is our example directive arguments
        directive_args = []

        # Template from mytardis with corresponding metdata brought across
        directive_args.append(['tardis://iant@tardis.edu.au/datafile/15',
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/',('a','5'), ('b','6')]])

        # Template on remote storage with corresponding multiple parameter sets
        directive_args.append(['hpc://iant@nci.edu.au/input/input.txt',
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/',('a','3'), ('b','4')],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/',('a','1'), ('b','2')],
            ['http://tardis.edu.au/schemas/hrmc/dfmeta2/',('c','hello')]])

        # A file (template with no variables)
        directive_args.append(['hpc://iant@nci.edu.au/input/file.txt',
            []])

        # A set of commands
        directive_args.append(['',['http://tardis.edu.au/schemas/hrmc/create',
            ('num_nodes','5'),('iseed','42')]])

        # Example of how a nci script might work.
        directive_args.append(['',
            ['http://nci.org.au/schemas/hrmc/custom_command/',('command','ls')]])

        def get_file(fname):
            """
            Fake the use urllib to retrieve the contents at the template and return
            as a string.  In reality, we would retrieve and cache here if possible.
            """
            logger.debug("fname=%s" % fname)
            if fname == "tardis://iant@tardis.edu.au/datafile/15":
                return "a={{a}} b={{b}}"
            elif fname == "hpc://iant@nci.edu.au/input/input.txt":
                return "a={{a}} b={{b}} c={{c}}"
            elif fname == "hpc://iant@nci.edu.au/input/file.txt":
                return "foobar"
            else:
                raise InvalidInputError("unknown file")

        def get_schema(sch_ns):
            logger.debug("sch_ns=%s" % sch_ns)
            s = models.Schema.objects.get(namespace=sch_ns)
            return s

        def mktempremote():
            """
            Create file to hold instantiated template for command execution.
            Kept local now, but could be on nci, nectar etc.

            """ 
            tf = tempfile.NamedTemporaryFile(delete=False)
            return tf

        def values_match_schema(schema, values):
            """ 
                Given a schema object and a set of (k,v) fields, checking
                each k has correspondingly named ParameterName in the schema
            """
            # TODO:
            return True

        command_args = []
        for darg in directive_args:
            logger.debug("darg=%s" % darg)
            file_url = darg[0]
            args = darg[1:]
            if file_url:
                f = get_file(file_url)
            context = {}
            if args:
                for a in args:
                    logger.debug("a=%s" % a)
                    if a:
                        sch = a[0]
                        schema = get_schema(sch)

                        values = a[1:]
                        logger.debug("values=%s" % values)
                        if not values_match_schema(schema, values):
                            raise InvalidInputError("specified parameters do not match schema")

                        for k,v in values:
                            # FIXME: need way of specifying ns and name in the template
                            # to distinuish between different templates. Here all the variables
                            # across entire template file must be disjoint
                            if not k:
                                raise InvalidInputError("Cannot have blank key in parameter set")

                            context["%s" % k] = v
            if file_url:
                logger.debug("file_url %s" % file_url)
                logger.debug("context = %s" % context)
                t = Template(f)
                con = Context(context)
                tmp_file = mktempremote() # FIXME: make remote
                tmp_file.write(t.render(con))    
                tmp_file.flush() 
                tmp_file.close()               
                command_args.append(("", tmp_file.name))
            else:
                for k,v in values:
                    command_args.append((k,v))

        logger.debug("command_args = %s" % command_args)

        self.assertEquals(len(command_args),6)
        for i,contents in ((0,"a=5 b=6"),(1,"a=1 b=2 c=hello"),(2,"foobar")):
            k,v = command_args[i]
            logger.debug("k=%s v=%s" % (k,v))
            self.assertFalse(k)
            f = open(v,"r").read()    
            logger.debug("f=%s" % f)    
            self.assertEquals(contents,f)
            os.remove(v)
        k,v = command_args[3]
        self.assertEquals(k,'num_nodes')
        self.assertEquals(v,'5')
        k,v = command_args[4]
        self.assertEquals(k,'iseed')
        self.assertEquals(v,'42')  # TODO: handle NUMERIC types correctly
        k,v = command_args[5]
        self.assertEquals(k,'command')
        self.assertEquals(v,'ls')



