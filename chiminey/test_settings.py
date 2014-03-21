from chiminey.settings_changeme import *

DEBUG=True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = "chiminey.urls"

TEMPLATE_DIRS = ["."]
INSTALLED_APPS += ('django_nose', )

NOSE_ARGS = ['--verbosity=3']


