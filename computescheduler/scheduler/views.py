# Create your views here.

from django.http import HttpResponse
from django.template import Context, loader

def hello(request):
    template = loader.get_template('hello.html')
    context = Context({
        'text': "world",
    })
    return HttpResponse(template.render(context))