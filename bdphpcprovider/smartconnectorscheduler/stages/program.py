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
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import sshconnector

logger = logging.getLogger(__name__)


class ProgramStage(Stage):
    """
    Execute a program remotely
    """
    command = ''
    def __init__(self, user_settings=None):
        self.user_settings = user_settings
        pass

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that triggered is idempotent.
        logger.debug("Program Stage Triggered")
        logger.debug("context=%s" % context)
        if 'program_output' in context:
            self.val = context['program_output']
        else:
            self.val = 0
        return True

    def process(self, context):
        """
        Execute a program with filearguments at the remote server
        """
        # TODO: make proper API for all external calls needed here

        logger.debug("Program Stage Processing")

        param_urls = [context[u"file%d" % x] for x in xrange(0, 3)]
        param_paths = [hrmcstages._get_remote_path(x, self.user_settings) for x in param_urls]

        program = context['program']

        logger.debug("program=%s" % program)
        logger.debug("remote paths=%s" % param_paths)

        # TODO: implement handling of config arguments

        self.command = "%s %s %s > %s " % (program, param_paths[0], param_paths[1], param_paths[2])

        # TODO: remotehost should be property of models.Platform, which can hold correct
        # ip address

        logger.debug("Concatenating command %s" % self.command)
        ssh = sshconnector.open_connection(ip_address=context['remotehost'], settings=self.user_settings)
        sshconnector.run_command(ssh, self.command, current_dir=self.user_settings[u'fsys'])

        logger.debug("context=%s" % context)

    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Program Stage Output")
        logger.debug("context=%s" % context)
        self.val += 1
        context['program_output'] = self.val
        return context

