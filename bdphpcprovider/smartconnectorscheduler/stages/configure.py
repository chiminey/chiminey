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


import os
import logging

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import smartconnector


logger = logging.getLogger(__name__)


class Configure(Stage, UI):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number

    def triggered(self, run_settings):
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/configure',
            'configure_done'):
            configure_done = int(run_settings[
                'http://rmit.edu.au/schemas/stages/configure'][u'configure_done'])
            return not configure_done
        return True

    def process(self, run_settings):
        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        self.contextid = int(run_settings[
            'http://rmit.edu.au/schemas/system'][u'contextid'])
        logger.debug("self.contextid=%s" % self.contextid)
        #TODO: we assume relative path BDP_URL here, but could be made to work
        # with non-relative (ie., remote paths)
        self.job_dir = run_settings[
            'http://rmit.edu.au/schemas/system/misc'][u'output_location']

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')

        input_location = run_settings[
            'http://rmit.edu.au/schemas/hrmc']['input_location']
        logger.debug("input_location=%s" % input_location)

        #prefix = "%s%s" % (self.job_dir, self.contextid)
        prefix = self.job_dir
        logger.debug("prefix=%s" % prefix)
        iter_inputdir = os.path.join(prefix, "input_0")
        logger.debug("iter_inputdir=%s" % iter_inputdir)
        source_url = smartconnector.get_url_with_pkey(self.boto_settings,
            input_location)
        logger.debug("source_url=%s" % source_url)
        destination_url = smartconnector.get_url_with_pkey(self.boto_settings,
            iter_inputdir, is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        hrmcstages.copy_directories(source_url, destination_url)

    def output(self, run_settings):

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/configure',
            {})[u'configure_done'] = 1
        # if not self._exists(run_settings,
        #         'http://rmit.edu.au/schemas/stages/configure'):
        #     run_settings['http://rmit.edu.au/schemas/stages/configure'] = {}
        # run_settings['http://rmit.edu.au/schemas/stages/configure']
        # [u'configure_done'] = True

        return run_settings
