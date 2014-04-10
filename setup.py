
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'docs/changes.rst')).read()

setup(
    name="chiminey",
    version="1.0",
    url='http://github.com/chiminey/chiminey',
    license='New BSD License',
    long_description=README + '\n\n' + CHANGES,
    author='Ian Thomas, Iman I. Yusuf, Heinrich W. Schmidt, Daniel Drumm, George Opletal',
    author_email='ianedwardthomas@gmail.com, iimanyusuf@gmail.com, h.w.schmidt.work@gmail.com, daniel.drumm@rmit.edu.au, g.opletal@gmail.com',
    packages=find_packages(),
    namespace_packages=['chiminey'],
    install_requires=[
        'setuptools',
        'django==1.4.5',
        'django-registration',
        'django-extensions',
        'django-form-utils',
        'django-haystack',
        'django-bootstrap-form',
        'celery==3.1.10',
        'django-celery==3.1.10',
        'django-kombu==0.9.4',
        'django-mptt',
        'django-storages',
        'requests==2.0',
        'django-widget-tweaks==1.3',
        'python-dateutil==2.2',
        'six==1.4.1',
        'paramiko==1.12.2',
        'boto>=2.5.2',
        'django-tastypie==0.9.15',
        'django-celery-with-redis==3.0',
        ],
    dependency_links=[
        'https://github.com/dahlia/wand/tarball/warning-bugfix#egg=Wand-0.1.10',
        'https://github.com/UQ-CMM-Mirage/django-celery/tarball/2.5#egg=django-celery-2.5.5',
        'https://github.com/defunkt/pystache/tarball/v0.5.2#egg=pystache-0.5.2'
    ],
)
