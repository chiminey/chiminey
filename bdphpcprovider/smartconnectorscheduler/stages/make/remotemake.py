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
import ast
import logging.config
from pprint import pformat


from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import platform

from bdphpcprovider.smartconnectorscheduler.smartconnector import multilevel_key_exists, get_existing_key
from . import setup_settings

logger = logging.getLogger(__name__)


class MakeRunStage(Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def input_valid(self, settings_to_test):
            return (True, "ok")

    def triggered(self, run_settings):
        if multilevel_key_exists(
            run_settings,
            'http://rmit.edu.au/schemas/stages/upload_makefile',
            'done'):
            try:
                upload_makefile_done = int(get_existing_key(run_settings,
                    'http://rmit.edu.au/schemas/stages/upload_makefile/done'))
            except ValueError, e:
                logger.error(e)
                return False
            if upload_makefile_done:
                if self._exists(
                        run_settings,
                        'http://rmit.edu.au/schemas/stages/make',
                        'program_success'):
                    program_success = int(run_settings[
                        'http://rmit.edu.au/schemas/stages/make'][u'program_success'])
                    logger.debug("program_success")
                    return not program_success
                else:
                    return True
        return False

    def process(self, run_settings):
        settings = setup_settings(run_settings)

        smartconnector.info(run_settings, "1: execute starting")

        def _get_dest_bdp_url(settings):
            return "%s@%s" % (
                    "nci",
                    os.path.join(settings['payload_destination'],
                                 str(settings['contextid'])))

        dest_url = _get_dest_bdp_url(settings)
        computation_platform_url = settings['comp_platform_url']
        bdp_username = settings['bdp_username']
        comp_pltf_settings = platform.get_platform_settings(
            computation_platform_url,
            bdp_username)
        logger.debug("comp_pltf_settings=%s" % pformat(comp_pltf_settings))
        settings.update(comp_pltf_settings)

        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            dest_url,
            is_relative_path=True,
            ip_address=settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_d_url)

        command = "cd %s; make %s" % (os.path.join(
                query_settings['root_path'],
                mypath),
            'startrun')
        logger.debug(command)
        command_out = ''
        errs = ''
        try:
            ssh = sshconnector.open_connection(
                ip_address=settings['host'],
                settings=settings)
            command_out, errs = sshconnector.run_command_with_status(
                ssh,
                command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
        if not errs:
            self.program_success = 1
        else:
            self.program_success = 0
        logger.debug("program_success =%s" % self.program_success)
        smartconnector.info(run_settings, "1: execute started")

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/make',
            {})[u'program_success'] = self.program_success
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/make',
            {})[u'running'] = 1
        return run_settings
