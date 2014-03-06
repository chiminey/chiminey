# Copyright (C) 2014, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
import logging.config
from urlparse import urlparse

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.defaultfilters import slugify

from chiminey.smartconnectorscheduler import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific strcture.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input("This will ERASE and reset the database. "
            " Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return

        # TODO: define precisely what thee groups allow
        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()
        self.group, _ = Group.objects.get_or_create(name="admin")
        self.group.save()
        self.group, _ = Group.objects.get_or_create(name="developer")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(
                codename="change_%s" % model_name)
            #delete_model = Permission.objects.get(codename="delete_%s" % model_name)
            #self.group.permissions.add(add_model)
            self.group.permissions.add(change_model)
            #self.group.permissions.add(delete_model)

        # TODO: refactor and clarify all these schemas
        schema_data = {
             u'http://rmit.edu.au/schemas/platform/storage/mytardis':
                [u'schema for Unix storage platform instances',
                {
                #u'name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'operation': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': 'update',  'ranking': 0, 'help_text': ''},
                u'filters': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '', 'ranking': 3, 'help_text': ''},
                u'platform_type': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': 'Platform type', 'initial': 'mytardis', 'ranking': 6, 'help_text': ''},
                u'platform_name': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'Platform name', 'initial': '',  'ranking': 10, 'help_text': ''},
                u'ip_address': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'IP address or Hostname', 'ranking':15, 'help_text':''},
                u'username': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Username', 'ranking':20, 'help_text':''},
                u'password': {'type':models.ParameterName.STRING, 'subtype':'password', 'description':'Password', 'ranking':31, 'help_text':''},
                #u'api_key': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'API key', 'ranking':42, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/storage/unix':
                [u'schema for Unix storage platform instances',
                {
                u'operation': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': 'update',  'ranking': 0, 'help_text': ''},
                u'filters': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '', 'ranking': 3, 'help_text': ''},
                u'platform_type': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': 'Platform type', 'initial': 'unix',  'ranking': 6, 'help_text': ''},
                u'platform_name': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'Platform name', 'initial': '',  'ranking': 10, 'help_text': ''},
                u'ip_address': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'IP address or Hostname', 'ranking':15, 'help_text':''},
                u'username': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Username', 'ranking':20, 'help_text':''},
                u'password': {'type':models.ParameterName.STRING, 'subtype':'password', 'description':'Password', 'ranking':22, 'help_text':''},
                u'home_path': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Home path', 'ranking':24, 'help_text':''},
                u'root_path': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Root path', 'ranking':33, 'help_text':''},
                u'private_key_path': {'type':models.ParameterName.STRING, 'subtype':'hidden', 'description':'', 'ranking':41, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/computation/cluster/pbs_based':
                [u'schema for Cluster-based or Unix-based computation platform instances',
                {
                #private keys are automatically generated by the Provider
                #u'name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'operation': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': 'update',  'ranking': 0, 'help_text': ''},
                u'filters': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '{}', 'ranking': 3, 'help_text': ''},
                u'platform_type': {'type': models.ParameterName.STRLIST, 'subtype': '', 'description': 'Platform type', 'initial': '', 'choices': '[("nci", "Cluster/Unix"), ]', 'ranking': 6, 'help_text': ''},
                u'platform_name': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'Platform name', 'initial': '',  'ranking': 10, 'help_text': ''},
                u'ip_address': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'IP address or Hostname', 'ranking':15, 'help_text':''},
                u'username': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Username', 'ranking':20, 'help_text':''},
                u'password': {'type':models.ParameterName.STRING, 'subtype':'password', 'description':'Password', 'ranking':22, 'help_text':''},
                u'home_path': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Home path', 'ranking':24, 'help_text':''},
                u'root_path': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'Root path', 'ranking':33, 'help_text':''},
                u'private_key_path': {'type':models.ParameterName.STRING, 'subtype':'hidden', 'description':'', 'ranking':41, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/computation/cloud/ec2-based':
                [u'schema for EC2-based cloud computing platform instances',
                {
                #private keys and security groups are automatically generated by the Provider
                u'platform_type': {'type': models.ParameterName.STRLIST, 'subtype': '', 'description': 'Platform Type', 'initial': '', 'choices': '[("nectar", "NeCTAR"), ("csrack", "CSRack"), ]', 'ranking': 0, 'help_text': ''},
                u'platform_name': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'Platform Name', 'initial': '',  'ranking': 1, 'help_text': ''},
                u'ec2_access_key': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'EC2 Access Key', 'initial': '',  'ranking': 3, 'help_text': ''},
                u'ec2_secret_key': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'EC2 Secret Key', 'initial': '', 'ranking': 5, 'help_text': ''},
                u'security_group': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '',  'ranking': 6, 'help_text': ''},
                u'private_key': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'ranking': 7, 'help_text':''},
                u'private_key_path': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '',  'ranking': 15, 'help_text': ''},
                u'vm_image_size': {'type': models.ParameterName.STRING, 'subtype': '', 'description': 'VM Image Size', 'initial': 'm1.small',  'ranking': 20, 'help_text': ''},
                u'operation': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': 'update',  'ranking': 24, 'help_text': ''},
                u'filters': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '{}', 'ranking': 30, 'help_text': ''},
                #u'name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/computation':
                [u'schema for computation platform instances',
                {
                u'offset': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 3, 'help_text':''},
                u'platform_url': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 1, 'help_text':''},
                u'namespace': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/storage/output':
                [u'schema for storage platform (output) instances',
                {
                u'offset': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 3, 'help_text':''},
                u'platform_url': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 1, 'help_text':''},
                u'namespace': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/platform/storage/input':
                [u'schema for storage platform (input) instances',
                {
                u'offset': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 3, 'help_text':''},
                u'platform_url': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking': 1, 'help_text':''},
                u'namespace': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''},
                }
                ],
            # u'http://rmit.edu.au/schemas//files':
            #     [u'general input files for directive',
            #     {
            #     u'file0': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
            #     u'file1': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
            #     u'file2': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
            #     }
            #     ],
            #  # Note that file schema ns must match regex
            #  # protocol://host/schemas/{directective.name}/files
            #  # otherwise files will not be matched correctly.
            #  # TODO: make fall back to directive files in case specfici
            #  # version not defined here.
            # u'http://rmit.edu.au/schemas/smartconnector1/files':
            #      [u'the smartconnector1 input files',
            #      {
            #      u'file0': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
            #      u'file1': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
            #      u'file2': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
            #      }
            #      ],
            # u'http://rmit.edu.au/schemas/hrmc/files':
            #      [u'the smartconnectorscheduler hrmc input files',
            #      {
            #      }
            #      ],
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                [u'the smartconnector1 create stage config',
                {
                u'iseed': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'num_nodes': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'null_number': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'parallel_number': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            # we might want to reuse schemas in muliple contextsets
            # hence we could merge next too corestages, for example.
            # However, current ContextParameterSets are unamed in the
            # URI so we can't identify which one to use.
            # TODO: testing schemas are probably deprecated
            u'http://rmit.edu.au/schemas/stages/null/testing':
                [u'the null stage internal testing',
                {
                u'output': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'index': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/parallel/testing':
                [u'the parallel stage internal testing',
                {
                u'output': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'index': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://nci.org.au/schemas/smartconnector1/custom':
                [u'the smartconnector1 custom command',
                {
                u'command': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/system':
                [u'Internal System',
                {
                u'platform': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'contextid': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                u'parentcontextid': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                u'random_numbers': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''},
                u'system': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'id': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'max_seed_int': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta':
                ["datafile",
                {
                u"a": {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'b': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta2':
                ["datafile2",
                {
                u'c': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/bdp_userprofile':
                ["UBDP user profile",
                {
                 u'username': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'BDP username', 'ranking':12, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/directive_profile':
                ["Directive profile",
                {
                 u'directive_name': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'Directive name', 'ranking':12, 'help_text':''},
                 u'sweep_name': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'Directive name', 'ranking':12, 'help_text':''},

                }
                ],
            # TODO: this schema is deprecated
            models.UserProfile.PROFILE_SCHEMA_NS:
                [u'user profile',
                {
                    u'nci_private_key': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'location of NCI private key', 'ranking':11, 'help_text':''},
                    u'nci_user': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'username for NCI access', 'ranking':10, 'help_text':''},
                    u'nci_password': {'type':models.ParameterName.STRING, 'subtype':'password',
                        'description':'password for NCI access', 'ranking':9, 'help_text':''},
                    u'nci_host': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'hostname for NCI', 'ranking':8, 'help_text':''},
                    u'flag': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'not used?', 'ranking':7, 'help_text':''},
                    u'nectar_private_key_name': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'name of the key for nectar', 'ranking':6, 'help_text':''},
                    u'nectar_private_key': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'location of NeCTAR private key', 'ranking':5, 'help_text':''},
                    u'nectar_ec2_access_key': {'type':models.ParameterName.STRING, 'subtype':'password',
                        'description':'NeCTAR EC2 Access Key', 'ranking':4, 'help_text':''},
                    u'nectar_ec2_secret_key': {'type':models.ParameterName.STRING, 'subtype':'password',
                        'description':'NeCTAR EC2 Secret Key', 'ranking':3, 'help_text':''},
                    u'mytardis_host': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'hostname for tardis (leave blank to not archive to mytardis)', 'ranking':2, 'help_text':''},
                    u'mytardis_user': {'type':models.ParameterName.STRING, 'subtype':'',
                        'description':'hostname for tardis', 'ranking':1, 'help_text':''},
                    u'mytardis_password': {'type':models.ParameterName.STRING, 'subtype':'password',
                        'description':'hostname for tardis', 'ranking':0, 'help_text':''},
                }
                ],
            # u'http://rmit.edu.au/schemas/copy/files':
            #      [u'the copy input files',
            #      {
            #      u'file0': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
            #      u'file1': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
            #      }
            #      ],
            # u'http://rmit.edu.au/schemas/program/files':
            #      [u'the copy input files',
            #      {
            #      u'file0': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
            #      u'file1': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
            #      u'file2': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
            #      }
            #      ],

            u'http://rmit.edu.au/schemas/stages/copy/testing':
                [u'the copy stage internal testing',
                {
                u'output': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/program/testing':
                [u'the program stage internal testing',
                {
                u'output': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/program/config':
                [u'the program command internal config',
                {
                u'program': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'remotehost': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'program_success': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/greeting/salutation':
                [u'salute',
                {
                u'salutation': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/reliability':
                [u'the schema for reliability framework',
                {
                u'cleanup_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/input/reliability':
                [u'Reliability',
                {
                u'maximum_retry': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'initial':2, 'ranking':1, 'description': 'Maximum Retries', 'help_text':'Enter the maximum number of retries'},
                u'reschedule_failed_processes': {'type':models.ParameterName.NUMERIC, 'subtype':'bool', 'ranking':2, 'initial':1, 'description': 'Reschedule failed processes', 'help_text': 'Select to reschedule any failed processes'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/system':
                [u'Locations',
                {
                u'input_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://127.0.0.1/myfiles/input', 'description':'Input Location', 'ranking':1,  'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'},
                u'output_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://local@127.0.0.1/sweep', 'description':'Output Location', 'ranking': 2, 'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'}
                }
                ],
            u'http://rmit.edu.au/schemas/input/location':
                [u'Locations',
                {
                u'input_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://127.0.0.1/myfiles/input', 'description':'Input Location', 'ranking':1,  'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'},
                u'output_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://local@127.0.0.1/sweep', 'description':'Output Location', 'ranking': 2, 'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'}
                }
                ],
            u'http://rmit.edu.au/schemas/input/location/input':
                [u'Locations',
                {
                u'input_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://127.0.0.1/myfiles/input', 'description':'Input Location', 'ranking':1,  'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/location/output':
                [u'Locations',
                {
                u'output_location': {'type':models.ParameterName.STRING, 'subtype':'storage_bdpurl', 'initial':'file://local@127.0.0.1/sweep', 'description':'Output Location', 'ranking': 2, 'help_text': 'Storage platform name with optional offset path: e.g., storage_home/myexperiment'}
                }
                ],
            u'http://rmit.edu.au/schemas/input/vasp':
                [u'VASP Smart Connector',
                {
                u'ncpus': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'initial':16, 'description':'Number of CPUs', 'ranking':1, 'help_text':''},
                u'project': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'h72', 'description':'Project Identifier', 'ranking':2, 'help_text':''},
                u'job_name': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'Si-FCC', 'description':'Job Name', 'ranking':3, 'help_text':''},
                u'queue': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'express', 'description':'Task Queue to use', 'ranking':4, 'help_text':''},
                u'walltime': {'type':models.ParameterName.STRING, 'subtype': 'timedelta', 'initial':'00:10:00', 'description':'Wall Time', 'ranking':5, 'help_text':''},
                u'mem': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'16GB', 'description':'Memory', 'ranking':6, 'help_text':''},
                u'max_iteration': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'description':'Maximum no. iterations', 'ranking':7, 'initial': 10, 'help_text':'Computation ends when either convergence or maximum iteration reached'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/system/compplatform':
                [u'Computation Platform',
                {
                u'computation_platform': {'type':models.ParameterName.STRLIST, 'subtype':'platform', 'initial': '', 'description':'Computation Platform Name', 'ranking':0, 'help_text':'The name of the computation platform to be used'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/system/cloud':
                [u'Cloud Resources',
                {
                u'number_vm_instances': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'initial':4, 'description':'Number of VM instances', 'ranking':1, 'help_text':''},
                u'minimum_number_vm_instances': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'initial':1, 'description':'Minimum No. VMs', 'ranking':2, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/input/mytardis':
                [u'MyTardis',
                {
                u'curate_data': {'type':models.ParameterName.NUMERIC, 'subtype':'bool', 'ranking':2, 'initial':1, 'description': 'Curate execution output', 'help_text': 'Curate data using selected MyTardis'},
                u'mytardis_platform': {'type':models.ParameterName.STRLIST, 'subtype':'mytardis', 'initial': 0, 'description':'MyTardis Platform', 'ranking':1, 'help_text':'Select MyTardis platfrom name'},
                u'experiment_id': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'initial': 0, 'description':'MyTardis experiment ID', 'ranking':0, 'help_text':'Use 0 for new experiment'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/hrmc':
                [u'HRMC Smart Connector',
                {
                u'iseed': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'Random Number Seed', 'ranking':0, 'initial': 42, 'help_text':'Initial seed for random numbers'},
                u'pottype': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'Pottype', 'ranking':10, 'help_text':'', 'initial':1},
                u'error_threshold': {'type':models.ParameterName.STRING, 'subtype':'float', 'description':'Error Threshold', 'ranking':23, 'initial':'0.03', 'help_text':'Delta for iteration convergence'},  # FIXME: should use float here
                u'optimisation_scheme': {'type':models.ParameterName.STRLIST, 'subtype':'choicefield', 'description':'No. varying parameters', 'ranking':45, 'choices': '[("MC","Monte Carlo"), ("MCSA", "Monte Carlo with Simulated Annealing")]', 'initial': 'MC', 'help_text':'', 'hidefield': 'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result', 'hidecondition':'== "MCSA"'},
                u'fanout_per_kept_result': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'No. fanout kept per result', 'initial': 1, 'ranking':52, 'help_text':''},
                u'threshold': {'type':models.ParameterName.STRING, 'subtype':'string', 'description':'No. results kept per iteration', 'ranking':60, 'initial':'[1]', 'help_text':'Number of outputs to keep between iterations. eg. [2] would keep the top 2 results.'}, # FIXME: should be list of ints
                u'max_iteration': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'description':'Maximum no. iterations', 'ranking':72, 'initial': 10, 'help_text':'Computation ends when either convergence or maximum iteration reached'},
                }
                ],
            u'http://rmit.edu.au/schemas/input/sweep':
                [u'Parameter Sweep',
                {
                u'sweep_map': {'type':models.ParameterName.STRING, 'subtype':'jsondict', 'initial': '{}', 'description':'Values to sweep over', 'ranking':1, 'help_text':'Dictionary of values to sweep over. e.g {\"var1\": [3, 7], \"var2\": [1, 2]} would result in 4 HRMC Jobs: [3,1] [3,2] [7,1] [7,2]'}
                }
                ],

            u'http://rmit.edu.au/schemas/stages/configure':
                [u'the configure state of the hrmc smart connector',
                {
                u'configure_done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/create':
                [u'the create state of the smartconnector1',
                {
                u'create_done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'ranking':12, 'help_text': ''},
                u'failed_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'ranking':11, 'help_text': ''},
                u'group_id': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':10, 'help_text':''},
                u'vm_size': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':9, 'help_text':''},
                u'vm_image': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':8, 'help_text':''},
                u'security_group': {'type':models.ParameterName.STRLIST, 'subtype':'', 'description':'', 'ranking':7, 'help_text':''},
                u'group_id_dir': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'cloud_sleep_interval': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':5, 'help_text':''},
                u'custom_prompt': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'nectar_username': {'type':models.ParameterName.STRING, 'subtype':'',
                    'description':'name of username for accessing nectar', 'ranking':3, 'help_text':''},
                u'nectar_password': {'type':models.ParameterName.STRING, 'subtype':'',
                    'description':'password of username for accessing nectar', 'ranking':2, 'help_text':''},
                u'created_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/setup':
                [u'the create stage of the smartconnector1',
                {
                u'filename_for_PIDs': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':5, 'help_text':''},
                u'setup_finished': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'payload_name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'payload_source': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'payload_destination': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/deploy':
                [u'the deploy stage of the smartconnector1',
                {
                u'started': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'deployed_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/bootstrap':
                [u'the bootstrap stage of the smartconnector1',
                {
                u'started': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'bootstrapped_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'bootstrap_done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/schedule':
                [u'the schedule stage of the smartconnector1',
                {
                u'rescheduled_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'ranking':11},
                u'procs_2b_rescheduled': {'type':models.ParameterName.STRING, 'subtype':'', 'ranking':10},
                u'total_rescheduled_procs': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'ranking':9},
                u'total_scheduled_procs': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':8, 'help_text':''},
                u'schedule_index': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':7, 'help_text':''},
                u'current_processes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'all_processes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':5, 'help_text':''},
                u'schedule_started': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'total_processes': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'scheduled_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'schedule_completed': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/execute':
                [u'the execute stage of the smartconnector1',
                {
                u'executed_procs': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/run':
                [u'the create stage of the smartconnector1',
                {
                u'runs_left': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':8, 'help_text':''},
                u'payload_cloud_dirname': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':7, 'help_text':''},
                u'compile_file': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'retry_attempts': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':5, 'help_text':''},
                u'error_nodes': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'initial_numbfile': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'rand_index': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'finished_nodes': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                u'run_map': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':0, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/transform':
                [u'the transform stage of the smartconnector1',
                {
                u'transformed': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/converge':
                [u'the converge stage of the smartconnector1',
                {
                u'converged': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'criterion': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},  # Use STRING as float not implemented
                }
                ],

            u'http://rmit.edu.au/schemas/stages/teardown':
                [u'the teardown stage of the smartconnector1',
                {
                u'run_finished': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],

            u'http://rmit.edu.au/schemas/stages/destroy':
                [u'the destroy stage of the smartconnector1',
                {
                u'run_finished': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/stages/sweep':
                [u'the sweep stage',
                {
                u'directive': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':4, 'help_text':''},
                u'template_name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                u'sweep_done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                }
                ],
            u'http://rmit.edu.au/schemas/hrmc/config':
                [u'configuration for hrmc connectors',
                {
                }
                ],
            # u'http://rmit.edu.au/schemas/sweep/files':
            #     [u'the smartconnectorscheduler hrmc input files',
            #     {
            #     }
            #     ],
            # u'http://rmit.edu.au/schemas/remotemake/files':
            #     [u'',
            #     {
            #     }
            #     ],
            u'http://rmit.edu.au/schemas/remotemake/config':
                [u'',
                {
                u'payload_destination': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'payload_source': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/upload_makefile':
                [u'the smartconnectorscheduler hrmc input files',
                {
                u'done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/wait':
                [u'wait stage parameters',
                {
                u'synchronous': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
                }
                ],
            u'http://rmit.edu.au/schemas/stages/make':
                [u'',
                {
                u'running': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''},
                u'program_success': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':2, 'help_text':''},
                u'runs_left': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':3, 'help_text':''},
                }
                ]
        }

        for ns in schema_data:
            l = schema_data[ns]
            logger.debug("l=%s" % l)
            desc = l[0]
            logger.debug("desc=%s" % desc)
            kv = l[1:][0]
            logger.debug("kv=%s", kv)

            url = urlparse(ns)
            print ns
            context_schema, _ = models.Schema.objects.get_or_create(
                namespace=ns,
                defaults={'name': slugify(url.path.replace('/', ' ')),
                          'description': desc})

            for k, v in kv.items():
                try:
                    model, _ = models.ParameterName.objects.get_or_create(
                        schema=context_schema,
                        name=k,
                        defaults=dict(v))
                except TypeError:
                    logger.debug('Parameters are added to a schema using old format.')
                # if 'hidefield' in dict(v):
                #     hidelinks[model.id] = dict(v)['hidefield']

        # print ("hidelinks=%s" % hidelinks)
        # for hidelink in hidelinks:
        #     pn = models.ParameterName.objects.get(id=hidelink)
        #     schema_ns, key_name = os.path.split(hidelinks[hidelink])
        #     print schema_ns
        #     try:
        #         schema = models.Schema.objects.get(namespace=str(schema_ns))
        #     except models.Schema.DoesNotExist, e:
        #         logger.error(e)
        #         logger.error(schema_ns)
        #         raise
        #     link_pn = models.ParameterName.objects.get(name=key_name, schema=str(schema))
        #     pn.hidefield = link_pn
        #     pn.save()

        # TODO: this platform code is superseeded by platfrom api and should
        # be removed.
        local_filesys_rootpath = settings.LOCAL_FILESYS_ROOT_PATH
        #local_filesys_rootpath = '/var/cloudenabling/remotesys'
        #nci_filesys_root_path = '/short/h72/BDP/BDP_payload'
        local_platform, _ = models.Platform.objects.get_or_create(name='local',
            root_path=local_filesys_rootpath)
        # nectar_platform, _ = models.Platform.objects.get_or_create(
        #     name='nectar', root_path='/home/centos')
        # nci_platform, _ = models.Platform.objects.get_or_create(
        #     name='nci', root_path=nci_filesys_root_path)

        logger.debug("local_filesys_rootpath=%s" % local_filesys_rootpath)

        #self.define_helloworld(local_filesys_rootpath)
        #self.define_copydir(local_filesys_rootpath)
        #self.define_smartconnector1(local_filesys_rootpath)

        #self.define_hrmc()
        #self.define_hrmc_sweep()

        #self.define_remote_make()
        #self.define_sweep_remotemake()

        #self.define_vasp()
        #self.define_sweep_vasp()

        #self.setup_directive_args()
        print "done"

    def define_hrmc(self):

        self.configure_package = "chiminey.corestages.configure.Configure"
        self.create_package = "chiminey.corestages.create.Create"
        self.bootstrap_package = "chiminey.corestages.bootstrap.Bootstrap"
        self.schedule_package = "chiminey.corestages.schedule.Schedule"
        self.execute_package = "chiminey.corestages.execute.Execute"
        self.wait_package = "chiminey.corestages.wait.Wait"
        self.transform_package = "chiminey.smartconnectorscheduler.stages.hrmc2.transform.Transform"
        self.converge_package = "chiminey.smartconnectorscheduler.stages.hrmc2.converge.Converge"
        self.destroy_package = "chiminey.corestages.destroy.Destroy"

        hrmc_composite_stage, _ = models.Stage.objects.get_or_create(name="hrmc_connector",
            description="Encapsultes HRMC smart connector workflow",
            package=self.hrmc_parallel_package,
            order=100)

        # FIXME: tasks.progress_context does not load up composite stage settings
        hrmc_composite_stage.update_settings({})

        hrmc_smart_dir, _ = models.Directive.objects.get_or_create(
            name="hrmc",
            description="A Hybrid Reverse Monte Carlo Smart Connector",
            hidden=True,
            stage=hrmc_composite_stage)

        configure_stage, _ = models.Stage.objects.get_or_create(name="configure",
            description="This is configure stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.configure_package,
            order=0)
        configure_stage.update_settings({
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
            })
        create_stage, _ = models.Stage.objects.get_or_create(name="create",
            description="This is create stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.create_package,
            order=1)
        create_stage.update_settings({u'http://rmit.edu.au/schemas/stages/create':
                {
                    u'vm_size': "m1.small",
                    u'vm_image': "ami-0000000d",
                    u'cloud_sleep_interval': 20,
                    u'security_group': '["ssh"]',
                    u'group_id_dir': 'group_id',
                    u'custom_prompt': '[smart-connector_prompt]$',
                    u'nectar_username': 'root',
                    u'nectar_password': ''
                }})
        bootstrap_stage, _ = models.Stage.objects.get_or_create(name="bootstrap",
            description="This is bootstrap stage of this smart connector",
            parent=hrmc_composite_stage,
            package=self.bootstrap_package,
            order=20)
        bootstrap_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/setup':
                {
                    u'payload_source': 'file://127.0.0.1/local/testpayload_new',
                    u'payload_destination': 'celery_payload_2',
                    u'payload_name': 'process_payload',
                    u'filename_for_PIDs': 'PIDs_collections',
                },
            })
        schedule_stage, _ = models.Stage.objects.get_or_create(name="schedule",
            description="This is schedule stage of this smart connector",
            parent=hrmc_composite_stage,
            package=self.schedule_package,
            order=25)
        execute_stage, _ = models.Stage.objects.get_or_create(name="execute",
            description="This is execute stage of this smart connector",
            parent=hrmc_composite_stage,
            package=self.execute_package,
            order=30)
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': 'HRMC2',
                    u'compile_file': 'HRMC',
                    u'retry_attempts': 3,
                    #u'max_seed_int': 1000,  # FIXME: should we use maxint here?
                    #u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
            })
        wait_stage, _ = models.Stage.objects.get_or_create(name="wait",
            description="This is wait stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.wait_package,
            order=40)
        wait_stage.update_settings({})

        transform_stage, _ = models.Stage.objects.get_or_create(name="transform",
            description="This is transform stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.transform_package,
            order=50)
        transform_stage.update_settings({})
        converge_stage, _ = models.Stage.objects.get_or_create(name="converge",
            description="This is converge stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.converge_package,
            order=60)
        converge_stage.update_settings({})
        destroy_stage, _ = models.Stage.objects.get_or_create(name="destroy",
            description="This is destroy stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.destroy_package,
            order=70)
        destroy_stage.update_settings({})

        # comm, _ = models.Command.objects.get_or_create(platform=nectar_platform,
        #     directive=hrmc_smart_dir, stage=hrmc_composite_stage)
        print "done"

    def define_sweep_vasp(self):

        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_make",
            description="Sweep Test",
            package="chiminey.corestages.sweep.Sweep",
            order=100)
        sweep_stage.update_settings({
            # FIXME: move random_numbers into system schema
            u'http://rmit.edu.au/schemas/system':
            {
                u'random_numbers': 'file://127.0.0.1/randomnums.txt'
            },

            })

        sweep, _ = models.Directive.objects.get_or_create(name="sweep_vasp",
            description="VASP Sweep Connector",
            stage=sweep_stage)

    def define_hrmc_sweep(self):
        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep",
            description="Sweep Test",
            package="chiminey.corestages.sweep.HRMCSweep",
            order=100)
        sweep_stage.update_settings(
                                    {
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'template_name': 'HRMC.inp',
                u'directive': 'hrmc'

            },
            # FIXME: move random_numbers into system schema
            u'http://rmit.edu.au/schemas/system':
            {
                u'random_numbers': 'file://127.0.0.1/randomnums.txt'
            },
            })
        # FIXME: tasks.progress_context does not load up composite stage settings
        sweep, _ = models.Directive.objects.get_or_create(name="sweep",
            description="HRMC Sweep Connector",
            stage=sweep_stage)

    def define_sweep_remotemake(self):

        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_make",
            description="Sweep Test",
            package="chiminey.corestages.sweep.RemoteMakeSweep",
            order=100)

        sweep_stage.update_settings({
            # FIXME: move random_numbers into system schema
            u'http://rmit.edu.au/schemas/system':
            {
                u'random_numbers': 'file://127.0.0.1/randomnums.txt'
            },
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'directive': "remotemake"
            }
            })
        sweep, _ = models.Directive.objects.get_or_create(name="sweep_make",
            description="Remote Make Sweep Connector",
            stage=sweep_stage)

    def setup_directive_args(self):
        sweep = models.Directive.objects.get(name="sweep")

        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system/cloud",
                RMIT_SCHEMA + "/input/reliability",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/hrmc",
                RMIT_SCHEMA + "/input/mytardis",
                RMIT_SCHEMA + "/input/sweep"
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(directive=sweep, order=i, schema=schema)

        sweep_make = models.Directive.objects.get(name="sweep_make")

        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/mytardis",
                RMIT_SCHEMA + "/input/sweep"
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(directive=sweep_make, order=i, schema=schema)

        sweep_make = models.Directive.objects.get(name="sweep_vasp")

        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/vasp",
                RMIT_SCHEMA + "/input/mytardis",
                RMIT_SCHEMA + "/input/sweep"
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(directive=sweep_make, order=i, schema=schema)

    def define_helloworld(self, local_filesys_rootpath):
        local_fs = FileSystemStorage(location=local_filesys_rootpath)
        self.copy_dir_stage = "chiminey.smartconnectorscheduler.stages.movement.CopyDirectoryStage"
        self.program_stage = "chiminey.smartconnectorscheduler.stages.program.LocalProgramStage"
        # Define all the corestages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copydir",
             description="data movemement operation",
             package=self.copy_dir_stage,
             order=100)
        copy_stage.update_settings({})
        program_stage, _ = models.Stage.objects.get_or_create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)
        program_stage.update_settings({})
        copy_dir, _ = models.Directive.objects.get_or_create(
            name="copydir",
            hidden=True,
            stage=copy_stage)
        program_dir, _ = models.Directive.objects.get_or_create(name="program",
            hidden=True,
            stage=program_stage)
        local_fs.save("local/greet.txt",
            ContentFile("{{salutation}} World"))
        local_fs.save("remote/greetaddon.txt",
            ContentFile("(remotely)"))

    def define_copydir(self, local_filesys_rootpath):
        self.copy_file_stage = "chiminey.smartconnectorscheduler.stages.movement.CopyFileStage"
        # Define all the corestages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copy",
             description="data movemement operation",
             package=self.copy_file_stage,
             order=100)
        copy_stage.update_settings({})
        copy_dir, _ = models.Directive.objects.get_or_create(
            name="copyfile",
            hidden=True,
            stage=copy_stage)

    def define_smartconnector1(self, local_filesys_rootpath):
        local_fs = FileSystemStorage(location=local_filesys_rootpath)
        self.null_package = "chiminey.smartconnectorscheduler.stages.nullstage.NullStage"
        self.parallel_package = "chiminey.smartconnectorscheduler.stages.composite.ParallelStage"
        self.hrmc_parallel_package = "chiminey.smartconnectorscheduler.stages.hrmc_composite.HRMCParallelStage"
        # Define all the corestages that will make up the command.  This structure
        # has two layers of composition
        composite_stage, _ = models.Stage.objects.get_or_create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)
        smart_dir, _ = models.Directive.objects.get_or_create(
            name="smartconnector1",
            hidden=True,
            stage=composite_stage)
        setup_stage, _ = models.Stage.objects.get_or_create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)
        # stage settings are usable from subsequent corestages in a run so only
        # need to define once for first null or parallel stage
        setup_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'null_number': 4,
                }
            })
        stage2, _ = models.Stage.objects.get_or_create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)
        stage2.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'parallel_number': 2
                }
            })
        models.Stage.objects.get_or_create(name="run1",
            parent=stage2,
            description="This is the running part 1",
            package=self.null_package,
            order=1)
        models.Stage.objects.get_or_create(name="run2",
            parent=stage2,
            description="This is the running part 2",
            package=self.null_package,
            order=2)
        models.Stage.objects.get_or_create(name="finished",
            parent=composite_stage,
            description="And here we finish everything off",
            package=self.null_package,
            order=3)
        local_fs.save("input/input.txt",
            ContentFile("a={{a}} b={{b}} c={{c}}"))
        local_fs.save("input/file.txt",
            ContentFile("foobar"))

    def define_vasp(self):
        smartpack = "chiminey.smartconnectorscheduler.stages"
        self.upload_makefile = smartpack + ".make.movement.MakeUploadStage"
        self.download_makefile = smartpack + ".make.movement.MakeDownloadStage"
        self.remotemake_stage = smartpack + ".make.remotemake.MakeRunStage"
        self.make_finished_stage = smartpack + ".make.makefinished.MakeFinishedStage"

        vasp_composite_stage, _ = models.Stage.objects.get_or_create(
            name="vasp_connector",
            description="VASP Connector",
            package=self.parallel_package,
            order=0)
        vasp_composite_stage.update_settings({})
        vasp, _ = models.Directive.objects.get_or_create(
            name="vasp", defaults={
                'stage': vasp_composite_stage,
                'description': "VASP Connector",
                'hidden': True})

        # TODO: need to build specific upload/download stages because no way
        # adapt to different connectors yet...

        # copies input files + makefile to remote system
        upload_makefile_stage, _ = models.Stage.objects.get_or_create(
            name="upload_makefile",
            description="upload payload to remote",
            package=self.upload_makefile,
            parent=vasp_composite_stage,
            order=1)
        upload_makefile_stage.update_settings(
            {
                'http://rmit.edu.au/schemas/remotemake/config':
                {
                    u'payload_destination': 'iet595/remotemake',
                    u'payload_source': 'file://127.0.0.1/vasppayload',
                }
            })
        # executes make with run target
        remotemake_stage, _ = models.Stage.objects.get_or_create(
            name="make",
            description="Makefile execution stage",
            package=self.remotemake_stage,
            parent=vasp_composite_stage,
            order=2)

        remotemake_stage.update_settings({})

        # executes make with finished target and repeats until finished.
        make_finished_stage, _ = models.Stage.objects.get_or_create(
            name="makefinished",
            description="Makefile execution stage",
            package=self.make_finished_stage,
            parent=vasp_composite_stage,
            order=3)
        logger.debug('make_finished_stage=%s' % str(make_finished_stage))
        make_finished_stage.update_settings({})

        # # copies input files + makefile to remote system
        # download_makefile_stage, _ = models.Stage.objects.get_or_create(
        #     name="download_makefile",
        #     description="download payload to remote",
        #     package=self.download_makefile,
        #     parent=vasp_composite_stage,
        #     order=4)
        # download_makefile_stage.update_settings({})

        # RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        # for i, sch in enumerate([
        #         RMIT_SCHEMA + "/input/system",
        #         RMIT_SCHEMA + "/input/mytardis",
        #         RMIT_SCHEMA + "/input/sweep"
        #         ]):
        #     schema = models.Schema.objects.get(namespace=sch)
        #     das, _ = models.DirectiveArgSet.objects.get_or_create(directive=vasp, order=i, schema=schema)

    def define_remote_make(self):
        smartpack = "chiminey.smartconnectorscheduler.stages"
        self.upload_makefile = smartpack + ".make.movement.MakeUploadStage"
        self.download_makefile = smartpack + ".make.movement.MakeDownloadStage"
        self.remotemake_stage = smartpack + ".make.remotemake.MakeRunStage"
        self.make_finished_stage = smartpack + ".make.makefinished.MakeFinishedStage"

        remote_make_composite_stage, _ = models.Stage.objects.get_or_create(
            name="remotemake_connector",
            description="Remote make file execution",
            package=self.parallel_package,
            order=0)
        remote_make_composite_stage.update_settings({})
        remote_make, _ = models.Directive.objects.get_or_create(
            name="remotemake",
            defaults={'stage': remote_make_composite_stage,
                      'description': "Remote execution of a Makefile",
                      'hidden': True})

        # TODO: need to build specific upload/download stages because no way
        # adapt to different connectors yet...

        # copies input files + makefile to remote system
        upload_makefile_stage, _ = models.Stage.objects.get_or_create(
            name="upload_makefile",
            description="upload payload to remote",
            package=self.upload_makefile,
            parent=remote_make_composite_stage,
            order=1)
        upload_makefile_stage.update_settings(
            {
                'http://rmit.edu.au/schemas/remotemake/config':
                {
                    u'payload_destination': 'iet595/remotemake',
                    u'payload_source': 'file://127.0.0.1/local/testpayload',
                }
            })
        # executes make with run target
        remotemake_stage, _ = models.Stage.objects.get_or_create(
            name="make",
            description="Makefile execution stage",
            package=self.remotemake_stage,
            parent=remote_make_composite_stage,
            order=2)

        remotemake_stage.update_settings({})

        # executes make with finished target and repeats until finished.
        make_finished_stage, _ = models.Stage.objects.get_or_create(
            name="makefinished",
            description="Makefile execution stage",
            package=self.make_finished_stage,
            parent=remote_make_composite_stage,
            order=3)
        logger.debug('make_finished_stage=%s' % str(make_finished_stage))
        make_finished_stage.update_settings({})

        # # copies input files + makefile to remote system
        # download_makefile_stage, _ = models.Stage.objects.get_or_create(
        #     name="download_makefile",
        #     description="download payload to remote",
        #     package=self.download_makefile,
        #     parent=remote_make_composite_stage,
        #     order=4)
        # download_makefile_stage.update_settings({})


        # RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        # for i, sch in enumerate([
        #         RMIT_SCHEMA + "/input/system",
        #         RMIT_SCHEMA + "/input/mytardis",
        #         RMIT_SCHEMA + "/input/sweep"
        #         ]):
        #     schema = models.Schema.objects.get(namespace=sch)
        #     das, _ = models.DirectiveArgSet.objects.get_or_create(directive=remote_make, order=i, schema=schema)

    def handle(self, *args, **options):
        self.setup()
        print "done"
