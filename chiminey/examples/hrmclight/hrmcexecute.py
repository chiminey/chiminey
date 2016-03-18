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
import os
import json
from chiminey.corestages import Execute
from chiminey.runsettings import update
from chiminey.storage import get_url_with_credentials, get_file
from chiminey.mytardis import create_dataset, create_paramset


logger = logging.getLogger(__name__)


class HRMCExecute(Execute):

    def set_domain_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
               '%s/input/hrmc/iseed' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/optimisation_scheme' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/pottype' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/fanout_per_kept_result' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/optimisation_scheme' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/pottype' % self.SCHEMA_PREFIX,
               '%s/system/max_seed_int' % self.SCHEMA_PREFIX,)