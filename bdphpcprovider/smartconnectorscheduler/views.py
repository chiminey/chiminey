# Create your views here.

from django.http import HttpResponse
from django.template import Context, RequestContext, loader
#from scribble import print_greeting
from mc import start
import json
import os

def index(request):
    from django.contrib import messages

    template = loader.get_template('index.html')
    context = RequestContext(request, {})
    if request.method == 'POST':
        input_parameters = request.POST
        stages = input_parameters['stages']
        group_id = str(input_parameters['group_id'])


        requested_stages_list=str(stages).split("'")
        print "Splitted ", requested_stages_list

        STAGES = ['Create', 'Setup', 'Run', 'Terminate']
        for stage in STAGES:
            if stage in requested_stages_list:
                if  stage == 'Create':
                    number_of_cores = input_parameters['number_of_cores']
                    group_id = start(['create', '-v', number_of_cores])
                    message = "Your group ID is %s" % group_id
                    callback(message)
                elif stage == 'Setup':
                    start(['setup', '-g', group_id])
                elif stage == 'Run':
                    zipped_input_dir = '/home/iman/myfile.zip'
                    extracted_input_dir = '/tmp/%s' % group_id
                    import base64
                    try:
                        encoded_input_dir = input_parameters['input_dir']
                        decoded_input_dir = base64.b64decode(encoded_input_dir)
                        f=open(zipped_input_dir,"wb")
                        f.write(decoded_input_dir)
                        f.close()
                        os.system('unzip -o -d %s %s' % (extracted_input_dir,
                                                      zipped_input_dir))
                        print 'Input Dir', extracted_input_dir
                        start(['run',
                               '-g', group_id,
                               '-i', extracted_input_dir+"/input",
                               '-o','/tmp/output5'])
                    except KeyError:
                        print 'Input directory not given.' \
                              ' Run stage is skipped'



                else:
                    print stage


        print "Done"

    return HttpResponse(template.render(context))


def callback(message):
    import urllib
    import urllib2
    url = "http://127.0.0.1:8001/apps/mytardis-hpc-app/response/"
    values = {'message': message}
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
    start(['create', '-v','1'])
    return HttpResponse(template.render(context))

def getoutput(request, file_id):
    """ Return an output fiel identified by file_id"""
    file_text = "this is the text for %s" % file_id
    return HttpResponse(file_text, mimetype='text/plain')
