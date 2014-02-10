# Copyright (C) 2013, RMIT University

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

from bdphpcprovider.smartconnectorscheduler import models

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
                [u'schema for NCI computation platform instances',
                {
                #private keys are automatically generated by the Provider
                #u'name': {'type':models.ParameterName.STRING, 'subtype':'', 'description':'', 'ranking':6, 'help_text':''},
                u'operation': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': 'update',  'ranking': 0, 'help_text': ''},
                u'filters': {'type': models.ParameterName.STRING, 'subtype': 'hidden', 'description': '', 'initial': '{}', 'ranking': 3, 'help_text': ''},
                u'platform_type': {'type': models.ParameterName.STRLIST, 'subtype': 'hidden', 'description': 'Platform type', 'initial': '', 'choices': '[("nci", "NCI"), ]', 'ranking': 6, 'help_text': ''},
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
            #      [u'the smartconnector hrmc input files',
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
            u'http://rmit.edu.au/schemas/input/vasp':
                [u'VASP Smart Connector',
                {
                u'ncpus': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'initial':16, 'description':'Number of CPUs', 'ranking':1, 'help_text':''},
                u'project': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'h72', 'description':'Project Identifier', 'ranking':2, 'help_text':''},
                u'job_name': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'Si-FCC', 'description':'Job Name', 'ranking':3, 'help_text':''},
                u'queue': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'express', 'description':'Task Queue to use', 'ranking':4, 'help_text':''},
                u'walltime': {'type':models.ParameterName.STRING, 'subtype': 'string', 'initial':'00:10:00', 'description':'Wall Time', 'ranking':5, 'help_text':''},
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
                u'pottype': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'Pottype', 'ranking':1, 'help_text':'', 'initial':1},
                u'max_iteration': {'type':models.ParameterName.NUMERIC, 'subtype':'whole', 'description':'Maximum no. iterations', 'ranking':2, 'initial': 10, 'help_text':'Computation ends when either convergence or maximum iteration reached'},
                u'error_threshold': {'type':models.ParameterName.STRING, 'subtype':'float', 'description':'Error Threshold', 'ranking':3, 'initial':'0.03', 'help_text':'Delta for iteration convergence'},  # FIXME: should use float here
                u'threshold': {'type':models.ParameterName.STRING, 'subtype':'string', 'description':'No. results kept per iteration', 'ranking':4, 'initial':'[1]', 'help_text':'Number of outputs to keep between iterations. eg. [2] would keep the top 2 results.'},  # FIXME: should be list of ints
                u'optimisation_scheme': {'type':models.ParameterName.STRLIST, 'subtype':'choicefield', 'description':'No. varying parameters', 'ranking':5, 'choices': '[("MC","Monte Carlo"), ("MCSA", "Monte Carlo with Simulated Annealing")]', 'initial': 'MC', 'help_text':'', 'hidefield': 'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result', 'hidecondition':'== "MCSA"'},
                u'iseed': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'Random Number Seed', 'ranking':7, 'initial': 42, 'help_text':'Initial seed for random numbers'},
                u'fanout_per_kept_result': {'type':models.ParameterName.NUMERIC, 'subtype':'natural', 'description':'No. fanout kept per result', 'initial': 1, 'ranking':12, 'help_text':''},
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
            #     [u'the smartconnector hrmc input files',
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
                [u'the smartconnector hrmc input files',
                {
                u'done': {'type':models.ParameterName.NUMERIC, 'subtype':'', 'description':'', 'ranking':1, 'help_text':''}
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

        #self.define_rand_number_sweep()

        self.define_rand_number()
        print "done"

    def define_rand_number_sweep(self):

        subdirective = models.Directive.objects.get(
            name="randomnumber"
        )

        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_rand",
            description="Sweep for Random",
            package="bdphpcprovider.examples.randomnumbers.randsweep.RandSweep",
            order=100)
        sweep_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'directive': subdirective.name
            }
            })
        sweep, _ = models.Directive.objects.get_or_create(name="sweep_rand",
            description="Rand Sweep Connector",
            stage=sweep_stage)

        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/mytardis",
                RMIT_SCHEMA + "/input/sweep",
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(
                  directive=sweep, order=i, schema=schema)

    def define_rand_number(self):
        package = "bdphpcprovider.examples.randomnumbers"
        randconfig = package + ".randconfig.RandConfig"
        randexecute = package + ".randexecute.RandExecute"
        randwait = package + ".randwait.RandWait"
        parent = "bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage"

        create_package = "bdphpcprovider.corestages.create.Create"
        bootstrap_package = "bdphpcprovider.corestages.bootstrap.Bootstrap"
        schedule_package = "bdphpcprovider.corestages.schedule.Schedule"

        destroy_package = "bdphpcprovider.corestages.destroy.Destroy"



        parent_stage, _ = models.Stage.objects.get_or_create(
            name="random_number_connector",
            description="Random number parent",
            package=parent,
            order=0)
        rand_config_stage, _ = models.Stage.objects.get_or_create(
            name="randconfig",
            description="Rand config stage",
            package=randconfig,
            parent=parent_stage,
            order=5
        )
        rand_config_stage.update_settings({})
        create_stage, _ = models.Stage.objects.get_or_create(name="create",
            description="This is create stage of HRMC smart connector",
            parent=parent_stage,
            package=create_package,
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
            parent=parent_stage,
            package=bootstrap_package,
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
            parent=parent_stage,
            package=schedule_package,
            order=25)
        rand_execute_stage, _ = models.Stage.objects.get_or_create(
            name="randexecute",
            description="Rand execute stage",
            package=randexecute,
            parent=parent_stage,
            order=10)
        rand_execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': '',
                    u'compile_file': '',
                    u'retry_attempts': 3,  # fixme remove after deleting references in all other stages
                },
            })
        rand_execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/setup':
                {
                    u'payload_source': '',
                    u'payload_destination': '',
                    u'payload_name': '',
                    u'filename_for_PIDs': 'PIDs_collections',
                },
            })
        rand_wait_stage, _ = models.Stage.objects.get_or_create(
            name="randwait",
            description="Rand wait stage",
            package=randwait,
            parent=parent_stage,
            order=15
        )
        rand_wait_stage.update_settings({})
        destroy_stage, _ = models.Stage.objects.get_or_create(name="destroy",
            description="This is destroy stage of HRMC smart connector",
            parent=parent_stage,
            package=destroy_package,
            order=70)
        destroy_stage.update_settings({})
        rand_number, _ = models.Directive.objects.get_or_create(
            name="randomnumber",
            defaults={'stage': parent_stage,
                      'description': "Random number generation",
                      'hidden': False}
        )
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(directive=rand_number, order=i, schema=schema)


        #self.define_rand_number_sweep()


    def handle(self, *args, **options):
        self.setup()
        print "done"


