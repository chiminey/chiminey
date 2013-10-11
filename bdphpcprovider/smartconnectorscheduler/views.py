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
# IN THE SOFTWARE.

# Create your views here.
import os
import fs

import logging
import logging.config
from pprint import pformat

from django.http import HttpResponse
from django.template import Context, RequestContext, loader
from django.conf import settings

#from bdphpcprovider.smartconnectorscheduler import mc
from bdphpcprovider.smartconnectorscheduler import models
from getresults import get_results
from bdphpcprovider.smartconnectorscheduler import hrmcstages

from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing, InvalidInputError

logger = logging.getLogger(__name__)


# def index(request):
#     print "language code", settings.LANGUAGE_CODE
#     template = loader.get_template('index.html')
#     context = RequestContext(request, {})
#     if request.method == 'POST':
#         input_parameters = request.POST
#         stages = input_parameters['stages']
#         experiment_id = input_parameters['experiment_id']
#         group_id = str(input_parameters['group_id'])
#         requested_stages_list=str(stages).split("'")
#         STAGES = ['Create', 'Setup', 'Run', 'Terminate']

#         for stage in STAGES:
#             if stage in requested_stages_list:
#                 if  stage == 'Create':
#                     number_of_cores = input_parameters['number_of_cores']
#                     group_id = mc.start(['create', '-v', number_of_cores])
#                     message = "Your group ID is %s" % group_id
#                     callback(message, stage, group_id)
#                     print "Create stage completed"
#                 elif stage == 'Setup':
#                     mc.start(['setup', '-g', group_id])
#                     message = "Setup stage completed"
#                     print message
#                     callback(message, stage, group_id)
#                 elif stage == 'Run':
#                     zipped_input_dir = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
#                     extracted_input_dir = '%s/%s' % (settings.BDP_INPUT_DIR_PATH, group_id)
#                     print "Extracted ", extracted_input_dir
#                     import base64
#                     try:
#                         encoded_input_dir = input_parameters['input_dir']
#                         decoded_input_dir = base64.b64decode(encoded_input_dir)
#                         f=open(zipped_input_dir,"wb")
#                         f.write(decoded_input_dir)
#                         f.close()
#                         command = 'unzip -o -d %s %s' % (extracted_input_dir,
#                                                          zipped_input_dir)
#                         os.system(command)
#                         output_dir = '%s/%s/output' % (settings.BDP_OUTPUT_DIR_PATH,
#                                                 group_id)

#                         os.system('rm -rf %s ' % output_dir)

#                         mc.start(['run',
#                                '-g', group_id,
#                                '-i', extracted_input_dir+"/input",
#                                '-o', output_dir])

#                         status = "RUNNING"
#                         while status == 'RUNNING':
#                             status = mc.start('check',
#                               '-g', group_id,
#                               '-o', output_dir)

#                         hrmc_output = [f for f in os.listdir(output_dir) if os.path.isdir(output_dir)
#                         and not f.endswith("_post")]

#                         absolute_output_dir = "%s/%s" % (output_dir, hrmc_output[0])
#                         print "Absolute path ", absolute_output_dir


#                         print "Getting results"


#                         get_results(experiment_id, group_id, absolute_output_dir)
#                         print "Getting results done"

#                         message = "Run stage completed. Results are ready"
#                         print message
#                         print "callback started"
#                         callback(message, stage, group_id)
#                         print "callback done"
#                     except KeyError:
#                         print 'Input directory not given.' \
#                               ' Run stage is skipped'
#                 else:
#                     mc.start(['teardown', '-g', group_id, 'yes'])
#                     message = "Terminate stage completed"
#                     print message
#                     callback(message, stage, group_id)
#         print "Done"
#     return HttpResponse(template.render(context))


def callback(message, stage, group_id):
    import urllib
    import urllib2
    url = settings.MYTARDIS_HPC_RESPONSE_URL
    values = {'message': message,
              'stage': stage,
              'group_id': group_id}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()


def hello(request):
    template = loader.get_template('hello.html')
    context = Context({
        'text': "world",
    })
    #print_greeting("Iman")
    #start(['create', '-v','1'])
    return HttpResponse(template.render(context))


def test_directive(request, directive_id):
    """
    Create example directives to be processed
    """
    if request.user.is_authenticated():
        directives = []
        platform = "nci"
        logger.debug("directive=%s" % directive_id)

        if directive_id == "1":
            # Instantiate a template locally, then copy to remote
            directive_name = "copy"
            logger.debug("%s" % directive_name)
            directive_args = []
            directive_args.append(
                ['file://local@127.0.0.1/local/greet.txt',
                    ['http://rmit.edu.au/schemas/greeting/salutation',
                        ('salutation', 'Hello Iman')]])
            directive_args.append(['ssh://nci@127.0.0.1/remote/greet.txt', []])
            directives.append((platform, directive_name, directive_args))

        elif directive_id == "2":
            # concatenate that file and another file (already remote) to form result
            directive_args = []
            directive_name = "program"
            logger.debug("%s" % directive_name)
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

        elif directive_id == "3":
            # transfer result back locally.
            directive_name = "copy"
            logger.debug("%s" % directive_name)
            directive_args = []
            directive_args.append(['ssh://nci@127.0.0.1/remote/greetresult.txt',
                []])
            directive_args.append(['file://local@127.0.0.1/local/finalresult.txt',
                []])

            directives.append((platform, directive_name, directive_args))

        elif directive_id == "4":
            directive_name = "smartconnector1"
            logger.debug("%s" % directive_name)
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

            directives.append((platform, directive_name, directive_args))

        elif directive_id == "5":
            platform = 'nectar'
            directive_name = "smartconnector_hrmc"
            logger.debug("%s" % directive_name)
            directive_args = []
            #local_fs_path = os.path.join(
            #    'bdphpcprovider', 'smartconnectorscheduler', 'testing', 'remotesys/').decode("utf8")

            directive_args.append(
                ['',
                    ['http://rmit.edu.au/schemas/hrmc',
                        ('number_vm_instances', 2), (u'iseed', 42),
                        # TODO: in configure stage could copy this information from somewhere to this required location
                        ('input_location',  'file://127.0.0.1/hrmcrun/input_0'),
                        ('number_dimensions', 1),
                        ('threshold', "[1]"),
                        ('error_threshold', "0.03"),
                        ('max_iteration', 20),
                        ('pottype', 1)
                    ]
                ])

            directives.append((platform, directive_name, directive_args))

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive=%s" % directives)
        new_run_contexts = []
        for (platform, directive_name, directive_args) in directives:
            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)

            try:
            # TODO: each user should only be have one outstanding task at a time (though system would work with more!)
                (run_settings, command_args, run_context) \
                    = hrmcstages.make_runcontext_for_directive(
                    platform,
                    directive_name,
                    directive_args, system_settings, request.user.username)
                new_run_contexts.append(str(run_context))

            except InvalidInputError, e:
                return HttpResponse(str(e))

    return HttpResponse("runs= %s" % pformat(new_run_contexts))



def getoutput(request, group_id, file_id):
    """ Return an output file identified by file_id"""
    # FIXME: add validation for group_id and file_id access

    output_dir = '%s/%s/output' % (settings.BDP_OUTPUT_DIR_PATH,
                                   group_id)
    hrmc_output = [f for f in os.listdir(output_dir) if os.path.isdir(output_dir)
    and not f.endswith("_post")]

    absolute_output_dir = "%s/%s" % (output_dir, hrmc_output[0])
    print "Absolute path ", absolute_output_dir

    file_text = open("%s/%s" % (absolute_output_dir, file_id)).read()
    return HttpResponse(file_text, mimetype='text/plain')
