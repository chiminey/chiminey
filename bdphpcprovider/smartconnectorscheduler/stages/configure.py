# Copyright (C) 2013, RMIT University

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

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_settings
from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing

import logging
logger = logging.getLogger(__name__)


class Configure(Stage, UI):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings

    def triggered(self, run_settings):
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/configure', 'configure_done'):
            return False
        return True

    def process(self, run_settings):
        pass

    def output(self, run_settings):

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/configure'):
            run_settings['http://rmit.edu.au/schemas/stages/configure'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/configure'][u'configure_done'] = True

        return run_settings
