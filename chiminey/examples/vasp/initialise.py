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

    def get_ui_schemas(self):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schemas = [
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/vasp",
                RMIT_SCHEMA + "/input/mytardis",
                ]
        return schemas

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

