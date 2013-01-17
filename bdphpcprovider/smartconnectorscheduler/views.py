# Create your views here.
import os
import fs

from django.http import HttpResponse
from django.template import Context, RequestContext, loader
from django.conf import settings

from bdphpcprovider.smartconnectorscheduler import mc
from getresults import get_results


def index(request):
    print "language code", settings.LANGUAGE_CODE
    template = loader.get_template('index.html')
    context = RequestContext(request, {})
    if request.method == 'POST':
        input_parameters = request.POST
        stages = input_parameters['stages']
        experiment_id = input_parameters['experiment_id']
        group_id = str(input_parameters['group_id'])
        requested_stages_list=str(stages).split("'")
        STAGES = ['Create', 'Setup', 'Run', 'Terminate']

        for stage in STAGES:
            if stage in requested_stages_list:
                if  stage == 'Create':
                    number_of_cores = input_parameters['number_of_cores']
                    group_id = mc.start(['create', '-v', number_of_cores])
                    message = "Your group ID is %s" % group_id
                    callback(message, stage, group_id)
                    print "Create stage completed"
                elif stage == 'Setup':
                    mc.start(['setup', '-g', group_id])
                    message = "Setup stage completed"
                    print message
                    callback(message, stage, group_id)
                elif stage == 'Run':
                    zipped_input_dir = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
                    extracted_input_dir = '%s/%s' % (settings.BDP_INPUT_DIR_PATH, group_id)
                    print "Extracted ", extracted_input_dir
                    import base64
                    try:
                        encoded_input_dir = input_parameters['input_dir']
                        decoded_input_dir = base64.b64decode(encoded_input_dir)
                        f=open(zipped_input_dir,"wb")
                        f.write(decoded_input_dir)
                        f.close()
                        command = 'unzip -o -d %s %s' % (extracted_input_dir,
                                                         zipped_input_dir)
                        os.system(command)
                        output_dir = '%s/%s/output' % (settings.BDP_OUTPUT_DIR_PATH,
                                                group_id)

                        os.system('rm -rf %s ' % output_dir)

                        mc.start(['run',
                               '-g', group_id,
                               '-i', extracted_input_dir+"/input",
                               '-o', output_dir])

                        status = "RUNNING"
                        while status == 'RUNNING':
                            status = mc.start('check',
                              '-g', group_id,
                              '-o', output_dir)

                        hrmc_output = [f for f in os.listdir(output_dir) if os.path.isdir(output_dir)
                        and not f.endswith("_post")]

                        absolute_output_dir = "%s/%s" % (output_dir, hrmc_output[0])
                        print "Absolute path ", absolute_output_dir


                        print "Getting results"


                        get_results(experiment_id, group_id, absolute_output_dir)
                        print "Getting results done"

                        message = "Run stage completed. Results are ready"
                        print message
                        print "callback started"
                        callback(message, stage, group_id)
                        print "callback done"
                    except KeyError:
                        print 'Input directory not given.' \
                              ' Run stage is skipped'
                else:
                    mc.start(['teardown', '-g', group_id, 'yes'])
                    message = "Terminate stage completed"
                    print message
                    callback(message, stage, group_id)
        print "Done"
    return HttpResponse(template.render(context))


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
