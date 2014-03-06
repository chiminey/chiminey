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


class RandInitial(CoreInitial):
    def define_execute_stage(self):
        '''
        overwrites the core execute stage definition
        '''
        execute_package = "chiminey.examples.randomnumbers.randexecute.RandExecute"
        execute_stage, _ = models.Stage.objects.get_or_create(
            name="randexecute",
            package=execute_package,
            parent=self.define_parent_stage(),
            defaults={'description': "This is the rand execute stage", 'order': 11})
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': '',
                    u'compile_file': '',
                    u'retry_attempts': 3,
                },
            })

    def attach_directive_args(self, new_directive):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/system/compplatform")
        das, _ = models.DirectiveArgSet.objects.get_or_create(
            directive=new_directive, order=1, schema=schema)
        schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/location/output")
        das, _ = models.DirectiveArgSet.objects.get_or_create(
            directive=new_directive, order=2, schema=schema)