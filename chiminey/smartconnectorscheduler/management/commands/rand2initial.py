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

        directive = Rand2Initial()
        directive.define_directive('random_number_cloud', description='Random Number Cloud Smart Connector')
        print "done"


    def handle(self, *args, **options):
        self.setup()
        print "done"


class Rand2Initial(CoreInitial):
    def define_parent_stage(self):
        parent_package = "chiminey.examples.randomnumbers2.rand2parent.Rand2Parent"
        parent_stage, _ = models.Stage.objects.get_or_create(name=self.get_parent_name(),
            description="Encapsultes HRMC2 smart connector workflow",
            package=parent_package,
            order=100)
        parent_stage.update_settings({})
        return parent_stage

    def define_configure_stage(self):
        configure_package = "chiminey.examples.randomnumbers2.rand2configure.Rand2Configure"
        configure_stage, _ = models.Stage.objects.get_or_create(
            name="rand2configure",
            description="This is the Rand2 configure stage",
            parent=self.define_parent_stage(),
            package=configure_package,
            order=0)
        configure_stage.update_settings({
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
        })
        return configure_stage

    def define_bootstrap_stage(self):
        bootstrap_stage = super(Rand2Initial, self).define_bootstrap_stage()
        bootstrap_stage.update_settings(
            {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': 'file://127.0.0.1/local/payload_randomnumber',
                        u'payload_destination': 'rand2_destination',
                        u'payload_name': 'process_payload',
                        u'filename_for_PIDs': 'PIDs_collections',
                    },
            })
        return bootstrap_stage

    def define_wait_stage(self):
        wait_stage = super(Rand2Initial, self).define_wait_stage()
        wait_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/wait':
                {
                    u'synchronous': 0
                },
        })
        return wait_stage

    def define_execute_stage(self):
        execute_stage = super(Rand2Initial, self).define_execute_stage()
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': '',
                    u'compile_file': '',
                    u'retry_attempts': 3,
                },
            })
        return execute_stage

    def define_transform_stage(self):
        transform_package = "chiminey.examples.randomnumbers2.rand2transform.Rand2Transform"
        transform_stage, _ = models.Stage.objects.get_or_create(name="rand2transform",
            description="This is the transform stage of Rand 2",
            parent=self.define_parent_stage(),
            package=transform_package,
            order=50)
        transform_stage.update_settings({})
        return transform_stage

    def attach_directive_args(self, new_directive):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system/cloud",
                RMIT_SCHEMA + "/input/location/output",
                RMIT_SCHEMA + "/input/mytardis",
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(
                directive=new_directive, order=i, schema=schema)

    def assemble_stages(self):
        self.define_transform_stage()
        self.define_converge_stage()
        return super(Rand2Initial, self).assemble_stages()
