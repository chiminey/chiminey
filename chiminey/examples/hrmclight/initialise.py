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
from chiminey.smartconnectorscheduler import models
from chiminey.initialisation import CoreInitial
from django.conf import settings as django_settings


logger = logging.getLogger(__name__)


class HRMCInitial(CoreInitial):
    def get_updated_parent_params(self):
        return {'package': "chiminey.examples.hrmclight.hrmcparent.HRMCParent"}

    def get_updated_configure_params(self):
        settings = \
            {
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
        }
        return { 'settings': settings}


    def get_ui_schema_namespace(self):
        schemas = [
                django_settings.INPUT_FIELDS['cloud'],
                django_settings.INPUT_FIELDS['location'],
                django_settings.INPUT_FIELDS['hrmclight'],
                django_settings.INPUT_FIELDS['reliability'],
                ]
        return schemas

    def get_domain_specific_schemas(self):
        #schema_data = #{
            #u'%s/input/hrmclight' % django_settings.SCHEMA_PREFIX:
        schema_data =  [u'HRMCLight Smart Connector',
             {
                 u'iseed': {'type': models.ParameterName.NUMERIC, 'subtype': 'natural',
                            'description': 'Random Number Seed', 'ranking': 0, 'initial': 42,
                            'help_text': 'Initial seed for random numbers'},
                 u'pottype': {'type': models.ParameterName.NUMERIC, 'subtype': 'natural', 'description': 'Pottype',
                              'ranking': 10, 'help_text': '', 'initial': 1},
                 u'error_threshold': {'type': models.ParameterName.STRING, 'subtype': 'float',
                                      'description': 'Error Threshold', 'ranking': 23, 'initial': '0.03',
                                      'help_text': 'Delta for iteration convergence'},
                 # FIXME: should use float here
                 u'optimisation_scheme': {'type': models.ParameterName.STRLIST, 'subtype': 'choicefield',
                                          'description': 'No. varying parameters', 'ranking': 45,
                                          'choices': '[("MC","Monte Carlo"), ("MCSA", "Monte Carlo with Simulated Annealing")]',
                                          'initial': 'MC', 'help_text': '',
                                          'hidefield': 'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result',
                                          'hidecondition': '== "MCSA"'},
                 u'fanout_per_kept_result': {'type': models.ParameterName.NUMERIC, 'subtype': 'natural',
                                             'description': 'No. fanout kept per result', 'initial': 1,
                                             'ranking': 52, 'help_text': ''},
                 u'threshold': {'type': models.ParameterName.STRING, 'subtype': 'string',
                                'description': 'No. results kept per iteration', 'ranking': 60, 'initial': '[1]',
                                'help_text': 'Number of outputs to keep between iterations. eg. [2] would keep the top 2 results.'},
                 # FIXME: should be list of ints
                 u'max_iteration': {'type': models.ParameterName.NUMERIC, 'subtype': 'whole',
                                    'description': 'Maximum no. iterations', 'ranking': 72, 'initial': 10,
                                    'help_text': 'Computation ends when either convergence or maximum iteration reached'},
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
