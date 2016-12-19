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


class JmtcInitial(CoreInitial):
    def get_updated_parent_params(self):
        return {'package': "chiminey.jmtc.jmtcparent.JmtcParent"}

    def get_updated_configure_params(self):
        settings = \
            {
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt',
                    u'metadata_builder': 'chiminey.mytardis.metadata.MetadataBuilder',
                },
        }
        return { 'settings': settings}



    def get_ui_schema_namespace(self):
        schemas = [
                django_settings.INPUT_FIELDS['cloud'],
                django_settings.INPUT_FIELDS['input_location'],
                django_settings.INPUT_FIELDS['output_location'],
                django_settings.INPUT_FIELDS['jmtc'],
                django_settings.INPUT_FIELDS['mytardis'],
                ]
        return schemas

#TODO backward compatability issue
    def get_domain_specific_schemas(self):

        schema_data =  [u'jmtc',
             {
                 u'jmtconnector_model_file': {'type': models.ParameterName.STRING, 'subtype': 'string',
                                'description': 'Model file name', 'ranking': 1, 'initial': '',
                                'help_text': 'Name of the model file for example file-name.jsimg placed in the input resource directory.'},
                 u'jmtconnector_jmt_tool': {'type': models.ParameterName.STRING, 'subtype': 'string',
                                'description': 'JMT Tool', 'ranking': 2, 'initial': '',
                                'help_text': 'Target JMT Tool corresponding to input file. Valid values are: JMVA or JSIM'},
                 #u'jmt_tool': {'type': models.ParameterName.STRLIST, 'subtype': 'choicefield',
                 #                         'description': 'JMT Tool', 'ranking': 20,
                 #                         'choices': '[("MVA","JMVA"), ("SIM", "JSIM")]',
                 #                         'initial': 'MVA', 'help_text': 'JMT Tool that will be used to process the input file'},
                 u'jmtconnector_jsim_seed': {'type': models.ParameterName.NUMERIC, 'subtype': 'natural',
                            'description': 'JSIM Simulation Seed', 'ranking': 3, 'initial': 0,
                            'help_text': 'Sets simulation seed for JSIM graph'},
                 u'jmtconnector_jsim_maxtime': {'type': models.ParameterName.NUMERIC, 'subtype': 'natural',
                            'description': 'JSIM MaxTime', 'ranking': 4, 'initial': 0,
                            'help_text': 'Set maximum simulation time for JSIM graph'},
                 u'additional_sweep_parameters': {'type': models.ParameterName.STRING, 'subtype': 'jsondict',
                                'description': 'Additional sweep parameters', 'ranking': 5, 'initial': '{}',
                                'help_text': 'Dictionary of values to sweep over, e.g {"var1":[3,7],"var2":[1,2]} would result in 4 Jobs:[3,1][3,2][7,1][7,2](JSON Dictionary)'},

             }
            ]
        #}
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
