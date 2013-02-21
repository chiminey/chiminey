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

from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.template import Context, Template
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from storages.backends.sftpstorage import SFTPStorage
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage


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


def _get_file(fname):
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


def _get_schema(sch_ns):
    logger.debug("sch_ns=%s" % sch_ns)
    s = models.Schema.objects.get(namespace=sch_ns)
    return s


def _get_remote_file_path(source_name):
    """
    Create file to hold instantiated template for command execution.
    Kept local now, but could be on nci, nectar etc.

    """

    # # The top of the remote filesystem that will hold a user's files
    remote_base_path = os.path.join("centos")

    from urlparse import urlparse
    o = urlparse(source_name)
    file_path = o.path.decode('utf-8')
    logger.debug("file_path=%s" % file_path)
    # if file_path[0] == os.path.sep:
    #     file_path = file_path[:-1]
    import uuid
    randsuffix = unicode(uuid.uuid4())  # should use some job id here

    relpath = u"%s_%s" % (file_path, randsuffix)

    if relpath[0] == os.path.sep:
        relpath = relpath[1:]
    logger.debug("relpath=%s" % relpath)

    # FIXME: for django storage, do we need to create
    # intermediate directories
    dest_path = os.path.join(remote_base_path, relpath)
    logger.debug("dest_path=%s" % dest_path)
    return dest_path.decode('utf8')


def values_match_schema(schema, values):
    """
        Given a schema object and a set of (k,v) fields, checking
        each k has correspondingly named ParameterName in the schema
    """
    # TODO:
    return True


class TestDirectiveCommands(TestCase):
    """
    Tests ability to translate directives with arguments
    into equivalent commands with correct template instantiated
    files and parameter type arguments
    """

    def setUp(self):
        self.remote_fs_path = os.path.join(
            os.path.dirname(__file__), '..', 'testing', 'remotesys').decode("utf8")
        logger.debug("self.remote_fs_path=%s" % self.remote_fs_path)
        self.remote_fs = FileSystemStorage(location=self.remote_fs_path)

    def tearDown(self):
        files = self._get_paths("")
        #logger.debug("files=%s", '\n'.join(files))
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

    def _load_data(self, params, paramtype):

        self.user = User.objects.create_user(username="username1",
            password="password")
        profile = models.UserProfile(
                      user=self.user)
        profile.save()

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

        context_schema = models.Schema.objects.create(
            namespace=models.Context.CONTEXT_SCHEMA_NS,
            name="Context Schema", description="Schema for a context")
        # We assume that a run_contest has only one schema at the moment, os
        # we have to load up this schema will all context values used in
        # any of the stages (and any parameters required for the stage
        # invocation)
        # TODO: allow multiple ContextParameterSet each with different schema
        # so each value will come from a namespace.  e.g., general/fsys
        # nectar/num_of_nodes, setup/nodes_setup etc.
        for name, param_type in {
            u'fsys': models.ParameterName.STRING,
            u'user_id': models.ParameterName.NUMERIC,
            u'file0': models.ParameterName.STRING,
            u'file1': models.ParameterName.STRING,
            u'file2': models.ParameterName.STRING,
            u'num_nodes': models.ParameterName.NUMERIC,
            u'iseed': models.ParameterName.NUMERIC,
            u'command': models.ParameterName.STRING,
            u'null_output': models.ParameterName.NUMERIC}.items():

            param = models.ParameterName.objects.create(schema=context_schema,
                name=name,
                type=param_type)

        param_set = models.UserProfileParameterSet.objects.create(user_profile=profile,
            schema=sch)
        for k, v in params.items():
            param_name = models.ParameterName.objects.create(schema=sch,
                name=k,
                type=paramtype[k])
            param = models.UserProfileParameter.objects.create(name=param_name,
                paramset=param_set,
                value=v)

        platform = models.Platform(name="nci")
        platform.save()

        directive = models.Directive(name="smartconnector1")
        directive.save()

        composite_stage = models.Stage.objects.create(name="basic_connector",
            description="encapsulates a workflow",
            package="bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage",
            order=100)

        null_stage = models.Stage.objects.create(name="null",
            description="Null Stage",
            package="bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage",
            order= 0
            )

        setup_stage = models.Stage.objects.create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package="bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage",
            order=0)
        run_stage = models.Stage.objects.create(name="run",
            parent=composite_stage,
            description="This is the running part",
            package="bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage",
            order=1)
        finished_stage = models.Stage.objects.create(name="finished",
            parent=composite_stage,
            description="And here we finish everything off",
            package="bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage",
            order=2)

        comm = models.Command(platform=platform, directive=directive, initial_stage=null_stage)
        comm.save()



    def _safe_import(self, path, args, kw):

        try:
            dot = path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured('%s isn\'t a filter module' % path)
        filter_module, filter_classname = path[:dot], path[dot + 1:]
        try:
            mod = import_module(filter_module)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing filter %s: "%s"' %
                                       (filter_module, e))
        try:
            filter_class = getattr(mod, filter_classname)
        except AttributeError:
            raise ImproperlyConfigured('Filter module "%s" does not define a "%s" class' %
                                       (filter_module, filter_classname))

        filter_instance = filter_class(*args, **kw)
        return filter_instance


    def test_simple(self):

        # setup all needed schemas below
        PARAMS = {'param1name': 'param1val',
            'param2name': 42}
        PARAMTYPE = {'param1name': models.ParameterName.STRING,
            'param2name': models.ParameterName.NUMERIC}
        self._load_data(PARAMS, PARAMTYPE)

        # Here is our example directive arguments
        directive_args = []

        # Template from mytardis with corresponding metdata brought across
        directive_args.append(['tardis://iant@tardis.edu.au/datafile/15',
            ['http://tardis.edu.au/schemas/hrmc/dfmeta/', ('a', 5), ('b', 6)]])

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
            ('num_nodes', 5), ('iseed', 42)]])

        # Example of how a nci script might work.
        directive_args.append(['',
            ['http://nci.org.au/schemas/hrmc/custom_command/', ('command', 'ls')]])

        command_args = []
        for darg in directive_args:
            logger.debug("darg=%s" % darg)
            file_url = darg[0].decode('utf8')
            args = darg[1:]
            if file_url:
                f = _get_file(file_url)
            context = {}
            if args:
                for a in args:
                    logger.debug("a=%s" % a)
                    if a:
                        sch = a[0].decode('utf8')
                        schema = _get_schema(sch)
                        values = a[1:]
                        logger.debug("values=%s" % values)
                        if not values_match_schema(schema, values):
                            raise InvalidInputError(
                                "specified parameters do not match schema")

                        for k, v in values:
                            # FIXME: need way of specifying ns and name in the template
                            # to distinuish between different templates. Here all the variables
                            # across entire template file must be disjoint
                            if not k:
                                raise InvalidInputError(
                                    "Cannot have blank key in parameter set")

                            try:
                                v_val = int(v)
                            except ValueError:
                                v_val = v.decode('utf8')  # as a string
                            context[k.decode('utf8')] = v_val
            if file_url:
                logger.debug("file_url %s" % file_url)
                logger.debug("context = %s" % context)
                # TODO: don't use temp file, use remote file with
                # name file_url with suffix based on the command job number?
                t = Template(f)
                con = Context(context)
                tmp_fname = _get_remote_file_path(file_url)  # FIXME: make remote
                cont = t.render(con)
                self.remote_fs.save(tmp_fname, ContentFile(cont.encode('utf-8')))  # NB: ContentFile only takes bytes
                command_args.append((u'', tmp_fname.decode('utf-8')))
            else:
                for k, v in values:
                    try:
                        v_val = int(v)
                    except ValueError:
                        v_val = v.decode('utf8')  # as a string
                    command_args.append((k.decode('utf8'), v_val))

        logger.debug("command_args = %s" % command_args)

        self.assertEquals(len(command_args), 6)
        for i, contents in ((0, "a=5 b=6"), (1, "a=1 b=2 c=hello"), (2, "foobar")):
            k, v = command_args[i]
            logger.debug("k=%s v=%s" % (k, v))
            self.assertFalse(k)
            f = self.remote_fs.open(v).read()
            logger.debug("f=%s" % f)
            self.assertEquals(contents, str(f))
            #os.remove(v)
        k, v = command_args[3]
        self.assertEquals(k, 'num_nodes')
        self.assertEquals(v, 5)
        k, v = command_args[4]
        self.assertEquals(k, 'iseed')
        self.assertEquals(v, 42)  # TODO: handle NUMERIC types correctly
        k, v = command_args[5]
        self.assertEquals(k, 'command')
        self.assertEquals(v, 'ls')


        platform = models.Platform.objects.get(name="nci")
        directive = models.Directive.objects.get(name="smartconnector1")
        command = models.Command.objects.get(directive=directive, platform=platform)

        initial_stage = command.initial_stage
        logger.debug("initial_stage=%s" % initial_stage)

        stage = self._safe_import(initial_stage.package,  [], {})
        logger.debug("stage=%s" % stage)

        # get the user
        user = User.objects.get(username="username1")
        profile = models.UserProfile.objects.get(user=user)

        # make run_context for this user
        run_context = models.Context.objects.create(owner=profile,
            current_stage=initial_stage)

        context_schema =_get_schema(models.Context.CONTEXT_SCHEMA_NS)
        logger.debug("context_schema=%s" % context_schema)
        # make a single parameter to represent the context
        param_set = models.ContextParameterSet.objects.create(context=run_context,
            schema= context_schema,
            ranking=0)

        # save initial context for current stage
        context = {}
        arg_num = 0
        for (k, v) in command_args:
            logger.debug("k=%s,v=%s" % (k, v))

            if k:
                context[k] = v
            else:
                key = u"file%s" % arg_num
                arg_num += 1
                context[key] = v
        context[u'fsys'] = self.remote_fs_path
        context[u'user_id'] = user.id
        logger.debug("context=%s" % context)
        run_context.update_context(context)

        # Main processing loop
        for run_context in models.Context.objects.all():
            # advance each users context one stage
            current_stage = run_context.current_stage
            logger.debug("current_stage=%s" % current_stage)
            stage = self._safe_import(current_stage.package,  [], {})  # obviously need to cache this
            logger.debug("stage=%s", stage)
            cont = run_context.get_context()
            logger.debug("retrieved cont=%s" % cont)
            user_settings = hrmcstages.retrieve_settings(cont)
            if stage.triggered(cont):
                logger.debug("triggered")
                stage.process(cont)
                cont = stage.output(cont)
                logger.debug("cont=%s" %  cont)
            else:
                logger.debug("not triggered")
            logger.debug("updated cont=%s" % cont)
            run_context.update_context(cont)
        logger.debug("finished main loop")

        res_context = {}
        for run_context in models.Context.objects.all():
            res_context.update(run_context.get_context())

        logger.debug("res_context =  %s" % res_context)

        context[u'null_output'] = 42
        logger.debug("context =  %s" % context)

        self.assertEquals(res_context, context)
        self.assertEquals(hrmcstages.retrieve_settings({u'user_id': user.id}),PARAMS )

# def main():

    # fs = NCIStorage(settings={'params': {'username':'centos',"password":'XXXX'},

    #                            'host':'115.146.94.198',

    #                            'root':'/home/centos/tmp/'})
