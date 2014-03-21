from os import path
from chiminey.settings_changeme import *

DATABASES = { 'default' :{
         'ENGINE': 'django.db.backends.sqlite3',
          'NAME': path.join(path.dirname(__file__),'test_chiminey.db'),               # Or path to database file if using sqlite3.
       	  'TEST_NAME':  path.join(path.dirname(__file__),'test_chiminey2.db')
         #'NAME': ':memory:',
         # 'USER': '',                      # Not used with sqlite3.
         # 'PASSWORD': '',                  # Not used with sqlite3.
         # 'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
         # 'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
 
     }
     }


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEMPLATE_DIRS = ["."]

#SOUTH_TESTS_MIGRATE = False


INSTALLED_APPS += ('django_nose', )

ROOT_URLCONF = "chiminey.urls"

# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.MD5PasswordHasher',
# )



