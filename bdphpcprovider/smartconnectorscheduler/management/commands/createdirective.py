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
from bdphpcprovider.smartconnectorscheduler.management.commands import randdirective, hrmcdirective
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific strcture.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input("This will ERASE and reset the database. "
            " Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return

        directive = randdirective.RandDirective()
        #directive.define_directive('randomnumber')
        directive.define_directive('sweep_rand', 'random_number', description='Random Number Sweep Connector')
        #directive = hrmcdirective.HRMCDirective()
        #directive.define_directive(name="hrmc2", description='Random number generation')
        print "done"


    def handle(self, *args, **options):
        self.setup()
        print "done"
