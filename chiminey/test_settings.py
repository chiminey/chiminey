from os import path
import sys
from chiminey.settings_changeme import *


DATABASES = {
    'default': {

    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:'
    }
}


# DATABASES = { 'default' :{
#          'ENGINE': 'django.db.backends.sqlite3',
#          'NAME': ':memory:',
#          #'NAME': path.join(path.dirname(__file__),'test_chiminey.db'),               # Or path to database file if using sqlite3.
#          #'TEST_NAME':  path.join(path.dirname(__file__),'test_chiminey2.db')
#          # 'USER': '',                      # Not used with sqlite3.
#          # 'PASSWORD': '',                  # Not used with sqlite3.
#          # 'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#          # 'PORT': '',                      # Set to empty string for default. Not used with sqlite3.

#      }
#      }


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEMPLATE_DIRS = ["."]

#SOUTH_TESTS_MIGRATE = False


INSTALLED_APPS = (
   'django_extensions',
   'django.contrib.auth',
   'django.contrib.contenttypes',
   'django.contrib.sessions',
   'django.contrib.sites',
   'django.contrib.messages',
   'django.contrib.admin',
   'django.contrib.admindocs',
   'django.contrib.markup',
   'django.contrib.staticfiles',
   'django.contrib.humanize',
   'django_nose',
   'storages',
   'djcelery',
   'djkombu',
   'tastypie',
   'widget_tweaks',
) + OUR_APPS


INSTALLED_APPS += ('south',)
INSTALLED_APPS += ('django_nose',)


print INSTALLED_APPS


#ROOT_URLCONF = "chiminey.urls"

# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.MD5PasswordHasher',
# )



