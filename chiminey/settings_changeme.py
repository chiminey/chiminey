import djcelery
import sys
import os

from datetime import timedelta

DEBUG = True

from os import path

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

#SUB_SITE = "chiminey"

MANAGERS = ADMINS

if 'test' in sys.argv:
    DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
        }
    }
    SOUTH_TESTS_MIGRATE = False

    NOSE_ARGS = [
        # turn on to always generate coverage report
        #'--with-coverage',
        #'--cover-package=chiminey.simpleui, chiminey.smartconnectorscheduler',
        #'--cover-inclusive',
        #'--with-yanc',
        #'--with-xtraceback',
        #'--logging-clear-handlers'
    ]
    LOCAL_FILESYS_ROOT_PATH = "/tmp/chiminey/tests"

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'bdphpc',
            'USER': 'bdphpc',
            'PASSWORD': 'bdphpc',  # unused with ident auth
            'HOST': '',
            'PORT': '',
        }
    }
    ROOT_URLCONF = 'chiminey.urls'
    LOCAL_FILESYS_ROOT_PATH = "/var/chiminey/remotesys"



LOGIN_REDIRECT_URL = "/jobs"

# Celery queue uses Django for persistence
BROKER_TRANSPORT = 'django'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None
TIME_ZONE = "Australia/Melbourne"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                            'smartconnectorscheduler/site_media').replace('\\', '/')

#STATIC_URL = path.join(path.dirname(__file__),'smra_portal/site_media').replace('\\','/')
#STATIC_URL = path.join('/site_media/').replace('\\','/')

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/site_media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'lpw@bqiq#lwcx0w=xo=j@z9#h!d&8svwz5fwv0_j1319^%92p_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware'
    )
VALUES_FNAME = 'values'

SMART_CONNECTORS = {
'hrmc': {'init': 'chiminey.examples.hrmc.initialise.HRMCInitial',
         'name': 'hrmc',
         'description': 'Hybrid Reverse Monte Carlo',
         'payload': '/opt/chiminey/current/chiminey/examples/hrmc/payload_hrmc',
         'sweep': True
         },
                    'hrmclite': {'init': 'chiminey.examples.hrmclite.initialise.HRMCInitial',
                             'name': 'hrmclite',
                             'description': 'Hybrid Reverse Monte Carlo without PSD',
                             'payload': '/opt/chiminey/current/chiminey/examples/hrmclite/payload_hrmc'
                             },
                    'wordcount': {'init': 'chiminey.examples.wordcount.initialise.WordCountInitial',
                                 'name': 'wordcount',
                                 'description': 'Counting words via Hadoop',
                                 'payload': '/opt/chiminey/current/chiminey/examples/wordcount/payload_wordcount',
                                 'args':('word_pattern',)
                                },
"randnum": {
           "name": "randnum",
           "init": "chiminey.examples.randnum.initialise.RandNumInitial",
           "description": "Randnum generator, with timestamp",
           "payload": "/opt/chiminey/current/chiminey/examples/randnum/payload_randnum"
            },
'prism':   {'init': 'chiminey.prismconnector.initialise.PrismInitial',
             'name': 'prism',
             'description': 'The PRISM Model Checker',
             'payload': '/opt/chiminey/current/chiminey/prismconnector/payload_prism',
             'sweep': True
             },
                    }

SCHEMA_PREFIX = "http://rmit.edu.au/schemas"

PAYLOAD_DESTINATION = 'active_payloads'


INPUT_FIELDS =  {'cloud': SCHEMA_PREFIX + "/input/system/compplatform/cloud",
                 'hadoop': SCHEMA_PREFIX + "/input/system/compplatform/hadoop",
                 'unix': SCHEMA_PREFIX + "/input/system/compplatform/unix",
                 'reliability': SCHEMA_PREFIX + "/input/reliability",
#                 'location':  SCHEMA_PREFIX + "/input/location",
                 'output_location': SCHEMA_PREFIX + "/input/location/output",
                 'input_location':  SCHEMA_PREFIX + "/input/location/input",
                 'hrmclite':  SCHEMA_PREFIX + "/input/hrmclite",
                 'hrmc':  SCHEMA_PREFIX + "/input/hrmc",
                 'wordcount':  SCHEMA_PREFIX + "/input/wordcount",
                 'mytardis':  SCHEMA_PREFIX + "/input/mytardis",
                 'prism':  SCHEMA_PREFIX + "/input/prism",
                 }

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path.join(path.dirname(__file__),
              'smartconnectorscheduler/templates/').replace('\\','/'),
    path.join(path.dirname(__file__),
              'smartconnectorscheduler/publish/').replace('\\','/'),
    path.join(path.dirname(__file__),
    'simpleui/templates/').replace('\\','/'),
)

TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
"django.core.context_processors.i18n",
"django.core.context_processors.media",
"django.core.context_processors.static",
"django.core.context_processors.tz",
'django.core.context_processors.request',
"django.contrib.messages.context_processors.messages")

OUR_APPS = ('chiminey.smartconnectorscheduler',
    'chiminey.simpleui')

def get_admin_media_path():
    import pkgutil
    package = pkgutil.get_loader("django.contrib.admin")
    return path.join(package.filename, 'static', 'admin')

ADMIN_MEDIA_STATIC_DOC_ROOT = get_admin_media_path()

# Static content location
STATIC_URL = '/static/'

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__),'..','static'))

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'

STATICFILES_DIRS = (
    ('admin', ADMIN_MEDIA_STATIC_DOC_ROOT),
)


AUTH_PROFILE_MODULE='smartconnectorscheduler.UserProfile'


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
    'storages',
    'djcelery',
    'djkombu',
    'tastypie',
    'widget_tweaks',
    'httpretty',
    'mock',
    'south',
    'django_nose',
) + OUR_APPS

#INSTALLED_APPS += ( 'south',)


#print '\n'.join(INSTALLED_APPS)

LOGGER_LEVEL = os.environ.get('LOGGER_LEVEL', 'WARN')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {

        'timestamped': {
            'format': ' [%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
            # 'format': '%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s: %(message)s'
        },

    },

    'handlers': {

        'default': {
            'class':'logging.StreamHandler',
            'formatter': 'timestamped'
            },



    },

    'loggers': {

        'chiminey': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
        },
        'chiminey.smartconnectorscheduler': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
        },
        'chiminey.sshconnection': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.platform': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.cloudconnection': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.reliabilityframework': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.simpleui': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.mytardis': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.simpleui.wizard': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.storage': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.sshconnector': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.core': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
        'chiminey.smartconnectorscheduler.tasks': {
            'level': 'INFO',
            'handlers': ['default'],
            },
        'celery.task': {
            'level': 'ERROR',
            'handlers': ['default'],
            },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['default'],
            },
        'south': {
            'level': LOGGER_LEVEL,
            'handlers': ['default'],
            },
    }
}


TASTYPIE_DEFAULT_FORMATS = ['json']

FIXTURE_DIRS = (
                path.join(path.dirname(__file__),
                          'smartconnectorscheduler/site_media').replace('\\', '/'),)


AUTH_PROFILE_MODULE = "smartconnectorscheduler.UserProfile"

LOGIN_URL = '/accounts/login'

SFTP_STORAGE_HOST = ""
SFTP_STORAGE_ROOT = ""
SFTP_STORAGE_PARAMS = {}

#CELERYBEAT_SCHEDULER="djcelery.schedulers.DatabaseScheduler"
# Warning: celeryd is not safe for muliple workers when backed by sqlite
CELERYBEAT_SCHEDULE = {
    # "test": {
    #     "task": "smartconnectorscheduler.test",
    #     "schedule": timedelta(seconds=15),
    # },
    "run_contexts": {
        "task": "smartconnectorscheduler.run_contexts",
        "schedule": timedelta(seconds=10)
        #"schedule": timedelta(seconds=60)
      },
    }


INTERNAL_IPS = ('127.0.0.1',)

FILE_UPLOAD_PERMISSIONS = 0700

# A MyTardis API endopoint
TEST_MYTARDIS_IP = ""
TEST_MTARDIS_USER = ""
TEST_MYTARDIS_PASSWORD = ""



# CLOUD CONFIGURATION



CSRACK_USERDATA = """#!/bin/bash
chmod 700 /etc/sudoers
sed -i '/requiretty/d' /etc/sudoers
chmod 440 /etc/sudoers
echo changedsudo
"""

# According to Nectar Image Catalog 12/4/14
VM_IMAGES = {
              #'csrack': {'placement': None, 'vm_image': "ami-00000004", 'user_data': CSRACK_USERDATA},
              'csrack': {'placement': None, 'vm_image': "ami-00000009", 'user_data': CSRACK_USERDATA}, # centos 7
              #'nectar': {'placement': None, 'vm_image': "ami-00001c06", 'user_data': ''},
              #'nectar': {'placement': None, 'vm_image': "ami-00001e2b", 'user_data': ''},
              'nectar': {'placement': 'monash-01', 'vm_image': "ami-000022b0", 'user_data': ''}, # centos 7
              'amazon': {'placement': '', 'vm_image': "ami-9352c1a9", 'user_data': ''}}


# CELERY CONFIGURATRION
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = {
  "hightasks": {
      "binding_key": "high",
      "exchange": "default",
  },
  "default": {
      "binding_key": "default",
      "exchange": "default",
  }
}
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "default"

CELERY_ROUTES = {
 "smartconnectorscheduler.context_message": {
  "queue": "hightasks",
  "routing_key": "high",
},
"smartconnectorscheduler.delete": {
  "queue": "hightasks",
  "routing_key": "high",
},
}


RESOURCE_SCHEMA_NAMESPACE = \
    {SCHEMA_PREFIX + '/input/system/compplatform/cloud': '/platform/computation/cloud/ec2-based',
     SCHEMA_PREFIX + '/input/system/compplatform/unix': '/platform/computation/cluster/pbs_based',
     SCHEMA_PREFIX + '/input/system/compplatform/hadoop': '/platform/computation/bigdata/hadoop',
     SCHEMA_PREFIX + '/input/location': '/platform/storage/filesystem/rfs',
     SCHEMA_PREFIX + '/input/location/input': '/platform/storage/filesystem/rfs',
     SCHEMA_PREFIX + '/input/location/output': '/platform/storage/filesystem/rfs',
     SCHEMA_PREFIX + '/input/mytardis': '/platform/storage/curation/mytardis',
    }



#BROKER_TRANSPORT = 'django'
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
REDIS_HOST = "localhost"

APIHOST = "http://127.0.0.1"

PLATFORM_CLASSES = (
    'chiminey.platform.rfs.RemoteFileSystemPlatform',
    'chiminey.platform.cloud.CloudPlatform',
    'chiminey.platform.jenkins.JenkinsPlatform',
    'chiminey.platform.mytardis.MyTardisPlatform',
    'chiminey.platform.hadoop.HadoopPlatform',
     )


djcelery.setup_loader()
