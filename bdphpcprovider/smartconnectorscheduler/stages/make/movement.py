
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


import logging
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import (
    Stage, get_url_with_pkey)
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector
from . import setup_settings

logger = logging.getLogger(__name__)


class MakeUploadStage(Stage):
    """
    copies directories from one location to another
    """
    def __init__(self, user_settings=None):
        pass

    def input_valid(self, settings_to_test):
        return (True, "ok")

    def triggered(self, run_settings):
        if self._exists(
                run_settings,
                'http://rmit.edu.au/schemas/stages/upload_makefile',
                'done'):
            upload_makefile_done = int(run_settings[
                'http://rmit.edu.au/schemas/stages/upload_makefile'][u'done'])
            return not upload_makefile_done
        return True

    def process(self, run_settings):
        """ perform the stage operation
        """
        settings = setup_settings(run_settings)
        encoded_s_url = get_url_with_pkey(settings, settings['input_location'])
        logger.debug("encoded_s_url=%s" % encoded_s_url)
        remote_path = "%s@%s_%s" % ("nci",
                                     settings['payload_destination'],
                                     settings['contextid'])
        logger.debug("Relative path %s" % remote_path)
        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            remote_path,
            is_relative_path=True,
            ip_address=run_settings[
                models.UserProfile.PROFILE_SCHEMA_NS]['nci_host'])
        logger.debug("destination_url=%s" % encoded_d_url)
        hrmcstages.copy_directories(encoded_s_url, encoded_d_url)

    def output(self, run_settings):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("CopyDirectory Stage Output")
        logger.debug("run_settings=%s" % run_settings)
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/upload_makefile',
            {})[u'done'] = 1
        return run_settings
