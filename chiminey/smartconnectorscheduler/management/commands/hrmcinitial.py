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
from django.core.management.base import BaseCommand
from chiminey.smartconnectorscheduler import models
from chiminey.initialisation import CoreInitial

logger = logging.getLogger(__name__)

MESSAGE = "This will add a new directive to the catalogue of available connectors.  Are you sure [Yes/No]?"


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific structure.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input(MESSAGE)
        if confirm != "Yes":
            print "action aborted by user"
            return

        directive = HRMCInitial()
        directive.define_directive('hrmc', description='HRMC Smart Connector', sweep=True)
        print "done"

    def handle(self, *args, **options):
        self.setup()
        print "done"


class HRMCInitial(CoreInitial):
    def define_parent_stage(self):
        hrmc_parallel_package = "chiminey.examples.hrmc2.hrmcparent.HRMCParent"
        hrmc_composite_stage, _ = models.Stage.objects.get_or_create(name=self.get_parent_name(),
            description="Encapsultes HRMC smart connector workflow",
            package=hrmc_parallel_package,
            order=100)
        hrmc_composite_stage.update_settings({})
        return hrmc_composite_stage

    def define_configure_stage(self):
        configure_package = "chiminey.examples.hrmc2.hrmcconfigure.HRMCConfigure"
        configure_stage, _ = models.Stage.objects.get_or_create(
            name="hrmcconfigure",
            description="This is the HRMC configure stage",
            parent=self.define_parent_stage(),
            package=configure_package,
            order=0)
        configure_stage.update_settings({
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'local/randomnums.txt'
                },
        })
        return configure_stage

    def define_bootstrap_stage(self):
        bootstrap_stage = super(HRMCInitial, self).define_bootstrap_stage()
        bootstrap_stage.update_settings(
            {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': 'local/payload_hrmc',
                        u'payload_destination': 'celery_payload_2',
                        u'payload_name': 'process_payload',
                        u'filename_for_PIDs': 'PIDs_collections',
                    },
            })
        return bootstrap_stage

    def define_execute_stage(self):
        execute_package = "chiminey.examples.hrmc2.hrmcexecute.HRMCExecute"
        execute_stage, _ = models.Stage.objects.get_or_create(name="hrmcexecute",
            description="This is the HRMC execute stage",
            parent=self.define_parent_stage(),
            package=execute_package,
            order=30)
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'process_output_dirname': 'HRMC2',
                    u'compile_file': 'HRMC',
                    u'retry_attempts': 3,
                },
            })
        return execute_stage

    def define_transform_stage(self):
        transform_package = "chiminey.examples.hrmc2.hrmctransform.HRMCTransform"
        transform_stage, _ = models.Stage.objects.get_or_create(name="hrmctransform",
            description="This is the transform stage of HRMC",
            parent=self.define_parent_stage(),
            package=transform_package,
            order=50)
        transform_stage.update_settings({})
        return transform_stage

    def define_converge_stage(self):
        converge_package = "chiminey.examples.hrmc2.hrmcconverge.HRMCConverge"
        converge_stage, _ = models.Stage.objects.get_or_create(name="hrmcconverge",
            description="This is the converge stage of HRMC",
            parent=self.define_parent_stage(),
            package=converge_package,
            order=60)
        converge_stage.update_settings({})
        return converge_stage

    def get_ui_schemas(self):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schemas = [
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system/cloud",
                RMIT_SCHEMA + "/input/reliability",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/hrmc",
                RMIT_SCHEMA + "/input/mytardis",
                ]
        return schemas

    def define_sweep_stage(self, subdirective):
        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_%s" % subdirective.name,
            description="Sweep for %s" % subdirective.name,
            package="chiminey.corestages.sweep.HRMCSweep",
            order=100)
        sweep_stage.update_settings(
                                    {
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
            })
        return sweep_stage

    def assemble_stages(self):
        self.define_transform_stage()
        self.define_converge_stage()
        return super(HRMCInitial, self).assemble_stages()
