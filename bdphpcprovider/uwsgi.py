import os,sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bdphpcprovider.settings")
sys.path.append(os.path.dirname(__file__))
sys.path.append('../lib/python2.6')
sys.path.append('../lib/python2.6/site-packages')
sys.path.append('../bin')
sys.path.append('../')
sys.path.append('../bdphpcprovider')

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
