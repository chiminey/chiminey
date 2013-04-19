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

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages



logger = logging.getLogger(__name__)


class LocalProgramStage(Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def triggered(self, run_settings):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that triggered is idempotent.
        logger.debug("Program Stage Triggered")
        logger.debug("run_settings=%s" % run_settings)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/program/testing', 'output'):
            self.val = run_settings['http://rmit.edu.au/schemas/stages/program/testing']['output']
        else:
            self.val = 0

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/program/config',
            'program_success'):
            return False

        return True

    def process(self, run_settings):
        """
        Execute a program with filearguments at the remote server
        """
        # TODO: make proper API for all external calls needed here

        logger.debug("Program Stage Processing")

        param_urls = [run_settings[u"http://rmit.edu.au/schemas/program/files"][u"file%d" % x] for x in xrange(0, 3)]

        program = run_settings[u"http://rmit.edu.au/schemas/program/config"]['program']
        platform = run_settings[u"http://rmit.edu.au/schemas/system"][u'platform']
        logger.debug("program=%s" % program)

        platform = models.Platform.objects.get(name=platform)
        logger.debug("platform=%s" % platform)

        # As this stage is associated with a COMMAND, which is specific to a platform, this
        # condition should always be True, though we might reuse the same Stage for different
        # platforms
        if platform.name == 'nci':
            bdp_urls = [smartconnector.get_url_with_pkey(self.user_settings, x) for x in param_urls]
            logger.debug("bdp_urls=%s" % bdp_urls)
            param_paths = [hrmcstages.get_remote_path(x) for x in bdp_urls]
            # FIXME: check that these param_paths are actually local to NCI and not elsewhere
            logger.debug("remote paths=%s" % param_paths)
            # TODO: implement handling of config arguments
            command = "%s %s %s > %s " % (program, param_paths[0], param_paths[1], param_paths[2])
            # TODO: remotehost should be property of models.Platform, which can hold correct
            # ip address

            remote_host = run_settings[u'http://rmit.edu.au/schemas/program/config'][u'remotehost']


            ssh = sshconnector.open_connection(ip_address=remote_host, settings={
                'private_key': self.user_settings['nci_private_key'],
                'username': self.user_settings['nci_user'],
                'password': self.user_settings['nci_password']})

            res, errs = sshconnector.run_command_with_status(ssh, command,
                current_dir=platform.root_path)
            if not errs:
                self.program_success = True
            else:
                self.program_success = False
            logger.debug("program_success =%s" % self.program_success)

        else:
            raise NotImplementedError("ProgramStage not supported for this platform")

        logger.debug("run_settings=%s" % run_settings)

    def output(self, run_settings):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Program Stage Output")
        logger.debug("run_settings=%s" % run_settings)
        self.val += 1
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/program/testing'):
            run_settings['http://rmit.edu.au/schemas/stages/program/testing'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/program/testing']['output'] = self.val
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/program/config'):
            run_settings['http://rmit.edu.au/schemas/program/config'] = {}
        run_settings['http://rmit.edu.au/schemas/program/config']['program_success'] = self.program_success
        return run_settings
