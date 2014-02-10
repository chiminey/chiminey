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
from bdphpcprovider.corestages import Execute, copy_settings
from bdphpcprovider.storage import get_url_with_pkey, list_dirs
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException


logger = logging.getLogger(__name__)


class HRMCExcute(Execute):
    def set_domain_settings(self, run_settings, local_settings):
        copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/iseed')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/threshold')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/pottype')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/threshold')
        copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/pottype')
