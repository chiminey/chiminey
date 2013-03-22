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
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


class ProgramStage(Stage):
    """
    Execute a program remotely
    """
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

        if self._exists(context, 'http://rmit.edu.au/schemas/stages/program/testing', 'output'):
            self.val = context['http://rmit.edu.au/schemas/stages/program/testing']['output']
        else:
            self.val = 0

        if self._exists(context, 'http://rmit.edu.au/schemas/program/config',
            'program_success'):
            return False

        return True

    def process(self, context):
        """
        Execute a program with filearguments at the remote server
        """
        # TODO: make proper API for all external calls needed here

        logger.debug("Program Stage Processing")

        param_urls = [context[u"http://rmit.edu.au/schemas/program/files"][u"file%d" % x] for x in xrange(0, 3)]
        param_paths = [_get_remote_path(x, self.user_settings) for x in param_urls]

        program = context[u"http://rmit.edu.au/schemas/program/config"]['program']
        platform = context[u"http://rmit.edu.au/schemas/system"][u'platform']
        logger.debug("program=%s" % program)
        logger.debug("remote paths=%s" % param_paths)

        platform = models.Platform.objects.get(name=platform)
        logger.debug("platform=%s" % platform)

        if platform.name == 'nci':
            # TODO: implement handling of config arguments
            command = "%s %s %s > %s " % (program, param_paths[0], param_paths[1], param_paths[2])
            # TODO: remotehost should be property of models.Platform, which can hold correct
            # ip address

            remote_host = context[u'http://rmit.edu.au/schemas/program/config'][u'remotehost']

            ssh = sshconnector.open_connection(ip_address=remote_host, settings=self.user_settings)
            res, errs = sshconnector.run_command_with_status(ssh, command, current_dir=self.user_settings[u'fsys'])
            if not errs:
                self.program_success = True
            else:
                self.program_success = False
            logger.debug("program_success =%s" % self.program_success)

        else:
            raise NotImplementedError("ProgramStage not supported for this platform")

        logger.debug("context=%s" % context)



    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Program Stage Output")
        logger.debug("context=%s" % context)
        self.val += 1

        if not self._exists(context, 'http://rmit.edu.au/schemas/stages/program/testing'):
            context['http://rmit.edu.au/schemas/stages/program/testing'] = {}

        context['http://rmit.edu.au/schemas/stages/program/testing']['output'] = self.val

        if not self._exists(context, 'http://rmit.edu.au/schemas/program/config'):
            context['http://rmit.edu.au/schemas/program/config'] = {}
        context['http://rmit.edu.au/schemas/program/config']['program_success'] = self.program_success


        return context



def _get_remote_path(file_url, user_settings):
    """
    Find the path at the remote site corresponding to file_url, but don't fetch
      # TODO: expand to return other parts of parsed url
    """
    logger.debug("file_url=%s" % file_url)

    # TODO: the path should be constructed from the Platform model, not from the user setttings.

    from urlparse import urlparse
    o = urlparse(file_url)
    scheme = o.scheme
    mypath = o.path
    logger.debug("scheme=%s" % scheme)
    logger.debug("mypath=%s" % mypath)

    if mypath[0] == os.path.sep:
        mypath = mypath[1:]
    logger.debug("mypath=%s" % mypath)

    if scheme == 'http':
        raise NotImplementedError("http scheme not implemented")
    elif scheme == "ssh":
        logger.debug("getting from hpc")
        remote_fs_path = user_settings['fsys']
        logger.debug("remote_fs_path=%s" % remote_fs_path)
        remote_path = os.path.join(remote_fs_path, mypath)

    elif scheme == "tardis":
        raise NotImplementedError("tardis scheme not implemented")
    elif scheme == "local":
        remote_fs_path = user_settings['fsys']
        remote_path = os.path.join(remote_fs_path, "/", mypath)
    else:
        raise errors.InvalidInputError()

    logger.debug("remote_path=%s" % remote_path)
    return remote_path


