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
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from . import setup_settings

logger = logging.getLogger(__name__)


class MakeFinishedStage(Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def input_valid(self, settings_to_test):
            return (True, "ok")

    def triggered(self, run_settings):

        if self._exists(
                run_settings,
                'http://rmit.edu.au/schemas/stages/make',
                u'running'):
            return run_settings['http://rmit.edu.au/schemas/stages/make'][
                u'running']
        return False

    def _job_finished(self, settings):
        remote_path = "%s@%s_%s" % ("nci",
                                     settings['payload_destination'],
                                     settings['contextid'])
        logger.debug("Relative path %s" % remote_path)
        remote_ip = settings['nci_host']

        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            remote_path,
            is_relative_path=True,
            ip_address=remote_ip)
        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_d_url)
        command = "cd %s; make %s" % (os.path.join(
                query_settings['root_path'], mypath),
            'running')
        command_out = ''
        errs = ''
        logger.debug("starting command %s for %s" % (command, remote_ip))
        try:
            ssh = sshconnector.open_connection(ip_address=remote_ip,
                                                settings=settings)
            command_out, errs = sshconnector.run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
        if not errs:
            self.program_success = True
        else:
            self.program_success = False

        logger.debug("program_success =%s" % self.program_success)

        # FIXME: Assume are done, then prove otherwise with "stillrunning"
        # but if remote has crashed, get no response, which should indicate
        # stopped running but in error stage?
        self.still_running = 0
        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if 'stillrunning' in line:
                    return False
        return True

    def process(self, run_settings):
        settings = setup_settings(run_settings)
        job_finished = self._job_finished(settings)
        if job_finished:
            self._get_output(settings)
            self.still_running = 0
        else:
            self.still_running = 1

    def _get_output(self, settings):
        """
            Retrieve the output from the task on the node
        """
        remote_path = "%s@%s_%s" % ("nci",
                                     settings['payload_destination'],
                                     settings['contextid'])
        logger.debug("Relative path %s" % remote_path)

        remote_ip = settings['nci_host']
        encoded_s_url = smartconnector.get_url_with_pkey(
            settings,
            remote_path,
            is_relative_path=True,
            ip_address=remote_ip)
        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_s_url)
        make_path = os.path.join(query_settings['root_path'], mypath)
        logger.debug("make_path=%s" % make_path)

        dest_url = settings[
            'output_location']

        logger.debug("Transferring output from %s to %s" % (remote_path,
            dest_url))
        logger.debug("dest_url=%s" % dest_url)
        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            dest_url, is_relative_path=False)
        logger.debug("encoded_d_url=%s" % encoded_d_url)

        hrmcstages.delete_files(encoded_d_url, exceptions=[])
        # FIXME: might want to turn on paramiko compress function
        # to speed up this transfer
        hrmcstages.copy_directories(encoded_s_url, encoded_d_url)

    def output(self, run_settings):
        run_settings['http://rmit.edu.au/schemas/stages/make']['running'] = self.still_running
        return run_settings