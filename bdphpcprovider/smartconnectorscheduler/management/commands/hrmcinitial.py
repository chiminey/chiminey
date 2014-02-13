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
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.management.commands.coreinitial import CoreInitial

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific structure.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input("This will ERASE and reset the database. "
            " Are you sure [Yes|No]")
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
        hrmc_parallel_package = "bdphpcprovider.smartconnectorscheduler.stages.hrmc_composite.HRMCParallelStage"
        hrmc_composite_stage, _ = models.Stage.objects.get_or_create(name="hrmc_connector",
            description="Encapsultes HRMC smart connector workflow",
            package=hrmc_parallel_package,
            order=100)
        hrmc_composite_stage.update_settings({})
        return hrmc_composite_stage

    def define_bootstrap_stage(self):
        bootstrap_stage = super(HRMCInitial, self).define_bootstrap_stage()
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
        return bootstrap_stage

    def define_wait_stage(self):
        wait_stage = super(HRMCInitial, self).define_wait_stage()
        wait_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/wait':
                {
                    u'synchronous': 0
                },
        })
        return wait_stage

    def define_execute_stage(self):
        execute_stage = super(HRMCInitial, self).define_execute_stage()
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': 'HRMC2',
                    u'compile_file': 'HRMC',
                    u'retry_attempts': 3,
                },
            })
        return execute_stage

    def attach_directive_args(self, new_directive):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system/cloud",
                RMIT_SCHEMA + "/input/reliability",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/hrmc",
                RMIT_SCHEMA + "/input/mytardis",
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(
                directive=new_directive, order=i, schema=schema)


    def define_sweep_stage(self, subdirective):
        sweep_stage = super(HRMCInitial, self).define_sweep_stage(subdirective)
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
        return sweep_stage

    def assemble_stages(self):
        self.define_transform_stage()
        self.define_converge_stage()
        return super(HRMCInitial, self).assemble_stages()