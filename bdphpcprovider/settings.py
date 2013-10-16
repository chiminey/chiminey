#Generated from Chef, do not modify
from bdphpcprovider.settings_changeme import *

DEBUG = True
Debug = True
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
            'filename': '/var/log/cloudenabling/bdphpcprovider.log',
            'formatter': 'timestamped'
        },
    },

    'loggers': {
        'bdphpcprovider.smartconnectorscheduler': {
            'handlers': ['file'],
            'level': 'DEBUG',
            },
        'bdphpcprovider.reliabilityframework': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        'bdphpcprovider.simpleui': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        'bdphpcprovider.core': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        }

}

#BROKER_TRANSPORT = 'django'
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
