from chiminey.settings_changeme import *

DEBUG=True
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.sqlite3',
     }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEMPLATE_DIRS = ["."]
INSTALLED_APPS += ('django_nose', )

ROOT_URLCONF = "chiminey.urls"

# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.MD5PasswordHasher',
# )



