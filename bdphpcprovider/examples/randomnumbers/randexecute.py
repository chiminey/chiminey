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
from bdphpcprovider.sshconnection import AuthError, SSHException
from bdphpcprovider.corestages import Execute
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status


class RandExecute(Execute):
    def run_task(self, ip_address, process_id, settings):
        settings['username'] = 'root'
        ssh = None
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            command, errs = run_command_with_status(ssh, 'uptime > /tmp/randtime')#fixme use platform location
        except (AuthError, SSHException, socket.error) as e:
            print e
        finally:
            if ssh:
                ssh.close()

    def output(self, run_settings):
        run_settings['http://rmit.edu.au/schemas/stages/run']['runs_left'] = 1
        return super(RandExecute, self).output()