# Copyright (C) 2016, RMIT University

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
from chiminey.smartconnectorscheduler import models
from chiminey.initialisation import CoreInitial
from django.conf import settings as django_settings


logger = logging.getLogger(__name__)


class RAC3DInitial(CoreInitial):
    def get_updated_parent_params(self):
        return {'package': "chiminey.3drac.3dracparent.RAC3DParent"}

    def get_updated_configure_params(self):
        settings = \
            {
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt',
                    u'metadata_builder': 'chiminey.mytardis.metadata.MetadataBuilder',
                },
        }
        return { 'settings': settings , 'package': "chiminey.3drac.3dracconfigure.RAC3DConfigure"}



    def get_ui_schema_namespace(self):
        schemas = [
                django_settings.INPUT_FIELDS['cloud'],
                django_settings.INPUT_FIELDS['input_location'],
                django_settings.INPUT_FIELDS['output_location'],
                django_settings.INPUT_FIELDS['3drac'],
                django_settings.INPUT_FIELDS['mytardis'],
                ]
        return schemas

    #TODO backward compatability issue
    def get_domain_specific_schemas(self):

        schema_data =  [u'3D Roughness Analysis Connector',
             {
                 u'data_file_name': {'type': models.ParameterName.STRING, 'subtype': 'string',
                                'description': 'Data file name', 'ranking': 20, 'initial': '',
                                'help_text': 'Input datafile name for Roughness Analysis e.g. filename.txt'},
                 u'virtual_blocks_list': {'type': models.ParameterName.STRING, 'subtype': 'string',
                                'description': 'Virtual blocks list', 'ranking': 80, 'initial': '',
                                'help_text': 'List of virtual blocks within the input datafile idicated by Cartesian coordinate for surface data and size of the block at each point e.g. [ [0,0,20], [10,14,10] ] - here for block size 20 at point 0,0 and block size 20 at point 10,14' },

             }
            ]
        return schema_data

    def get_updated_sweep_params(self, subdirective):
        package = "chiminey.corestages.sweep.HRMCSweep"
        settings = {
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'template_name': 'HRMC.inp',
                u'directive': subdirective.name

            },
            # FIXME: move random_numbers into system schema
            u'http://rmit.edu.au/schemas/system':
            {
                u'random_numbers': 'file://127.0.0.1/randomnums.txt'
            },
            }
        return {'package': package, 'settings': settings}
