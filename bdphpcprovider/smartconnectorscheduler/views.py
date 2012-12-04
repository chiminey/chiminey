# Create your views here.

from django.http import HttpResponse
from django.template import Context, RequestContext, loader
#from scribble import print_greeting
from mc import start
import json

def index(request):
    from django.contrib import messages

    template = loader.get_template('index.html')
    context = RequestContext(request, {})
    if request.method == 'POST':
        input_parameters = request.POST
        stages = input_parameters['stages']
        group_id = input_parameters['group_id']
        number_of_cores = input_parameters['number_of_cores']

        requested_stages_list=str(stages).split("'")
        print "Splitted ", requested_stages_list



        print str(stages)
        print group_id, str(group_id)

        STAGES = ['Create', 'Setup', 'Run', 'Terminate']
        for stage in STAGES:
            if stage in requested_stages_list:
                if  stage == 'Create':
                    group_id = start(['create', '-v', number_of_cores])
                    callback(group_id)
                else:
                    print stage


        print "MySide", input_parameters, input_parameters['stages']

    return HttpResponse(template.render(context))


def callback(new_group_id):
    import urllib
    import urllib2
    url = "http://127.0.0.1:8001/apps/mytardis-hpc-app/response/"
    values = {'group_id': new_group_id}
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
