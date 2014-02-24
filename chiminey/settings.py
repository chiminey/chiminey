#Generated from Chef, do not modify
from chiminey.settings_changeme import *

DEBUG=True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bdphpc',
        'USER': 'bdphpc',
        'PASSWORD': 'bdphpc', # unused with ident auth
        'HOST': '',
        'PORT': '',
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamped': {
            'format': '%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s: %(message)s'
        },
    },

    'handlers': {
        'file': {
            'level':'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/cloudenabling/chiminey.log',
            'formatter': 'timestamped'
        },
    },
    'loggers': {
        'chiminey.smartconnectorscheduler': {
            'handlers': ['file'],
            'level': 'DEBUG',
            },
        'chiminey.reliabilityframework': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        'chiminey.simpleui': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        'chiminey.core': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        }
}


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

LOCAL_FILESYS_ROOT_PATH = "/var/cloudenabling/remotesys"
#BROKER_TRANSPORT = 'django'
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
import djcelery
djcelery.setup_loader()