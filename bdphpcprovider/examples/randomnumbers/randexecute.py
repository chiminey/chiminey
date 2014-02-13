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
from bdphpcprovider.corestages import Execute
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status


logger = logging.getLogger(__name__)

class RandExecute(Execute):
    #fixme: should removed out after execute is refactored
    def set_domain_settings(self, run_settings, local_settings):
        pass

    def run_task(self, ip_address, process_id, local_settings, run_settings):
        logger
        filename = 'rand'
        output_path = self.get_process_output_path(run_settings, process_id, local_settings)
        logger.debug('output_path=%s' % output_path)
        ssh = open_connection(ip_address=ip_address, settings=local_settings)
        try:
            command, errs = run_command_with_status(
                ssh, "mkdir -p %s; cd %s ;"
                     " python -c 'import random; "
                     "print random.random()' > %s" %
                     (output_path, output_path, filename))
            logger.debug('command=%s errs=%s' % (command, errs))
        finally:
            ssh.close()