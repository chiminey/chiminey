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

import os
import logging
from pprint import pformat

# from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage

from bdphpcprovider.platform import manage
from bdphpcprovider import messages
from bdphpcprovider import compute
from bdphpcprovider import storage

from . import setup_settings
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.runsettings import getval, setvals, SettingNotFoundException
from bdphpcprovider.corestages import stage


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class MakeRunStage(stage.Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def input_valid(self, settings_to_test):
            return (True, "ok")


    def is_triggered(self, run_settings):
        try:
            upload_makefile_done = int(getval(run_settings, '%s/stages/upload_makefile/done' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            return False

        if upload_makefile_done:
            try:
                program_success = int(getval(run_settings, '%s/stages/make/program_success' % RMIT_SCHEMA))
            except (ValueError, SettingNotFoundException):
                return True

            logger.debug("program_success")
            return not program_success

        return False

        # if smartconnector.multilevel_key_exists(
        #     run_settings,
        #     'http://rmit.edu.au/schemas/stages/upload_makefile',
        #     'done'):
        #     try:
        #         upload_makefile_done = int(smartconnector.get_existing_key(run_settings,
        #             'http://rmit.edu.au/schemas/stages/upload_makefile/done'))
        #     except ValueError, e:
        #         logger.error(e)
        #         return False
        #     if upload_makefile_done:
        #         if self._exists(
        #                 run_settings,
        #                 'http://rmit.edu.au/schemas/stages/make',
        #                 'program_success'):
        #             program_success = int(run_settings[
        #                 'http://rmit.edu.au/schemas/stages/make'][u'program_success'])
        #             logger.debug("program_success")
        #             return not program_success
        #         else:
        #             return True
        # return False

    def process(self, run_settings):
        settings = setup_settings(run_settings)
        messages.info(run_settings, "1: execute starting")

        def _get_dest_bdp_url(settings):
            return "%s@%s" % (
                    "nci",
                    os.path.join(settings['payload_destination'],
                                 str(settings['contextid'])))

        dest_url = _get_dest_bdp_url(settings)
        computation_platform_url = settings['comp_platform_url']
        bdp_username = settings['bdp_username']
        comp_pltf_settings = manage.get_platform_settings(
            computation_platform_url,
            bdp_username)
        logger.debug("comp_pltf_settings=%s" % pformat(comp_pltf_settings))
        settings.update(comp_pltf_settings)
        encoded_d_url = stage.get_url_with_pkey(
            settings,
            dest_url,
            is_relative_path=True,
            ip_address=settings['host'])
        (scheme, host, mypath, location, query_settings) = \
            storage.parse_bdpurl(encoded_d_url)
        stderr = ''
        try:
            ssh = open_connection(
                ip_address=settings['host'],
                settings=settings)
            (command_out, stderr) = compute.run_make(ssh, (os.path.join(
                    query_settings['root_path'],
                    mypath)), 'startrun')
        except Exception, e:
            logger.error(e)
            raise
        finally:
            if ssh:
                ssh.close()
        self.program_success = int(not stderr)
        logger.debug("program_success =%s" % self.program_success)
        messages.info(run_settings, "1: execute started")

    def output(self, run_settings):

        # TODO: should only set runnning if program_success is true?
        setvals(run_settings, {
                '%s/stages/make/program_success' % RMIT_SCHEMA: self.program_success,
                '%s/stages/make/running' % RMIT_SCHEMA: 1
                })

        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/make',
        #     {})[u'program_success'] = self.program_success
        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/make',
        #     {})[u'running'] = 1
        return run_settings
