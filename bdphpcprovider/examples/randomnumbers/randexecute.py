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

import socket
import os
import logging
from bdphpcprovider.sshconnection import AuthError, SSHException
from bdphpcprovider.corestages import Execute
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status


logger = logging.getLogger(__name__)

class RandExecute(Execute):
    def set_domain_settings(self, run_settings, local_settings):
        pass

    def prepare_inputs(self, local_settings, output_storage_settings,
                        computation_platform_settings, mytardis_settings):
        pass

    def run_task(self, ip_address, process_id, settings, run_settings):
        ssh = None
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            computation_platform = self.get_platform_settings(
                run_settings, 'http://rmit.edu.au/schemas/platform/computation')
            logger.debug('ssh=%s' % ssh)
            logger.debug('computation_platform=%s' % computation_platform)
            filename = 'rand'
            output_path = os.path.join(
                computation_platform['root_path'], settings['payload_destination'],
                str(process_id), settings['payload_cloud_dirname'])
            logger.debug('output_path=%s' % output_path)
            command, errs = run_command_with_status(ssh, "mkdir -p %s; cd %s ; "
                                                         "python -c 'import random; print random.random()' > %s" %
                                                         (output_path, output_path, filename))
            #'python -c \'import random; print random.random()\'
            logger.debug('command=%s errs=%s' % (command, errs))
        except (AuthError, SSHException, socket.error) as e:
            logger.error(e)
            raise
        finally:
            if ssh:
                ssh.close()

    def output(self, run_settings):
        run_settings['http://rmit.edu.au/schemas/stages/run']['runs_left'] = 1
        return super(RandExecute, self).output(run_settings)