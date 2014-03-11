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

logger = logging.getLogger(__name__)


class VASPInitial(CoreInitial):

    def define_bootstrap_stage(self):
        bootstrap_stage = super(VASPInitial, self).define_bootstrap_stage()
        bootstrap_stage.update_settings(
            {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': 'local/payload_vasp',
                        u'payload_destination': 'chiminey_demo',
                    },
            })
        return bootstrap_stage

    def define_execute_stage(self):
        execute_stage = super(VASPInitial, self).define_execute_stage()

        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'process_output_dirname': 'vasp',
                },
            })
        return execute_stage

    def define_transform_stage(self):
        transform_package = "chiminey.examples.vasp.vasptransform.VASPTransform"
        transform_stage, _ = models.Stage.objects.get_or_create(name="vasptransform",
            description="This is the transform stage of VASP",
            parent=self.define_parent_stage(),
            package=transform_package,
            order=50)
        transform_stage.update_settings({})
        return transform_stage

    def get_ui_schema_namespace(self):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schemas = [
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/vasp",
                RMIT_SCHEMA + "/input/mytardis",
                ]
        return schemas

    def get_domain_specific_schemas(self):
        schema_data = {
            u'http://rmit.edu.au/schemas/input/vasp':
            [u'VASP Smart Connector',
             {
                 u'ncpus': {'type': models.ParameterName.NUMERIC, 'subtype': 'whole', 'initial': 16,
                            'description': 'Number of CPUs', 'ranking': 1, 'help_text': ''},
                 u'project': {'type': models.ParameterName.STRING, 'subtype': 'string', 'initial': 'h72',
                              'description': 'Project Identifier', 'ranking': 2, 'help_text': ''},
                 u'job_name': {'type': models.ParameterName.STRING, 'subtype': 'string', 'initial': 'Si-FCC',
                               'description': 'Job Name', 'ranking': 3, 'help_text': ''},
                 u'queue': {'type': models.ParameterName.STRING, 'subtype': 'string', 'initial': 'express',
                            'description': 'Task Queue to use', 'ranking': 4, 'help_text': ''},
                 u'walltime': {'type': models.ParameterName.STRING, 'subtype': 'timedelta', 'initial': '00:10:00',
                               'description': 'Wall Time', 'ranking': 5, 'help_text': ''},
                 u'mem': {'type': models.ParameterName.STRING, 'subtype': 'string', 'initial': '16GB',
                          'description': 'Memory', 'ranking': 6, 'help_text': ''},
                 u'max_iteration': {'type': models.ParameterName.NUMERIC, 'subtype': 'whole',
                                    'description': 'Maximum no. iterations', 'ranking': 7, 'initial': 10,
                                    'help_text': 'Computation ends when either convergence or maximum iteration reached'},
             }
            ],
        }
        return schema_data

    def define_sweep_stage(self, subdirective):
        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_%s" % subdirective.name,
            description="Sweep for %s" % subdirective.name,
            package="chiminey.examples.vasp.vaspsweep.VASPSweep",
            order=100)
        sweep_stage.update_settings(
                                    {
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'template_name': 'VASP.inp',  # FIXME: probably don't need this
                u'directive': 'vasp'

            },
            })
        return sweep_stage

