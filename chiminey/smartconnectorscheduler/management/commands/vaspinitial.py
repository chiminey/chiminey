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
from chiminey.smartconnectorscheduler.management.commands.coreinitial import CoreInitial

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

        directive = VASPInitial()
        directive.define_directive('vasp', description='VASP Smart Connector', sweep=True)
        print "done"

    def handle(self, *args, **options):
        self.setup()
        print "done"


class VASPInitial(CoreInitial):

    def define_bootstrap_stage(self):
        bootstrap_stage = super(VASPInitial, self).define_bootstrap_stage()
        bootstrap_stage.update_settings(
            {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': 'file://127.0.0.1/payload_vasp',
                        u'payload_destination': 'chiminey_demo',
                    },
            })
        return bootstrap_stage

    def define_wait_stage(self):
        wait_stage = super(VASPInitial, self).define_wait_stage()
        wait_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/wait':
                {
                    u'synchronous': 0
                },
        })
        return wait_stage

    def define_execute_stage(self):
        execute_stage = super(VASPInitial, self).define_execute_stage()

        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': 'vasp',
                    u'compile_file': 'VASP',
                    u'retry_attempts': 3,
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

    def attach_directive_args(self, new_directive):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        for i, sch in enumerate([
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system",
                RMIT_SCHEMA + "/input/vasp",
                RMIT_SCHEMA + "/input/mytardis",
                ]):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(
                directive=new_directive, order=i, schema=schema)

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

    def assemble_stages(self):
        self.define_transform_stage()
        self.define_converge_stage()
        return super(VASPInitial, self).assemble_stages()
