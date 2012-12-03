# Create your views here.

from django.http import HttpResponse
from django.template import Context, loader
#from scribble import print_greeting
from mc import start

def hello(request):
    template = loader.get_template('hello.html')
    context = Context({
        'text': "world",
    })
    #print_greeting("Iman")
    start(['create', '-v','1'])
    return HttpResponse(template.render(context))