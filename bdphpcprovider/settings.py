#Generated from Chef, do not modify
from bdphpcprovider.settings_changeme import *

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
        }
}

CELERYBEAT_SCHEDULE = {
    #"test": {
    #    "task": "smartconnectorscheduler.test",
    #    "schedule": timedelta(seconds=15),
    #},
    "run_contexts": {
        "task": "smartconnectorscheduler.run_contexts",
        "schedule": timedelta(seconds=15)
      },
    }
