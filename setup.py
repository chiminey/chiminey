
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'docs/changes.rst')).read()

setup(
    name="cloudenabling",
    version="0.99",
    url='http://github.com/mytardis/mytardis',
    license='MIT License',
    long_description=README + '\n\n' + CHANGES,
    author='Ian Thomas',
    author_email='Ian.Edward.Thomas@rmit.edu.au',
    packages=find_packages(),
    namespace_packages=['bdphpcprovider'],
    install_requires=[
        'setuptools',
        'django==1.4.1',
        'django-registration',
        'django-extensions',
        'django-form-utils',
        'django-haystack',
        'django-bootstrap-form',
        'celery==2.5.5',           # Delayed tasks and queues
        'django-celery==2.5.5',
        'django-kombu',
        'decisiontree',
        'django-mptt'
        ],
    dependency_links = [
        'https://github.com/dahlia/wand/tarball/warning-bugfix#egg=Wand-0.1.10',
        'https://github.com/UQ-CMM-Mirage/django-celery/tarball/2.5#egg=django-celery-2.5.5',
        'https://github.com/defunkt/pystache/tarball/v0.5.2#egg=pystache-0.5.2'
    ],
    entry_points = {
       'console_scripts': [
            'mc = cloudenable.mc:start',
       ],
    }
)
