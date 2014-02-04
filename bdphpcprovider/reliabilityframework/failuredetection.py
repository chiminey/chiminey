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
from bdphpcprovider.cloudconnection import get_this_vm
#from paramiko import BadHostKeyException, AuthenticationException, SSHException
from bdphpcprovider.sshconnection import AuthError, BadHostKeyException, AuthenticationException, SSHException
import socket

logger = logging.getLogger(__name__)


class FailureDetection():
    def sufficient_vms(self, created_vms, min_number_vms):
        if int(created_vms) < int(min_number_vms):
            logger.error('Insufficient no. VMs created')
            logger.info('created_nodes=%d but minimmum_requirement=%d'
                        % (created_vms, min_number_vms))
            return False
        return True

    def failed_ssh_connection(self, exception):
        logger.debug('exception is %s ' % exception.__class__)
        try:
            logger.debug(exception.__class__)
            raise exception.__class__
        except (AuthError, BadHostKeyException, AuthenticationException,
                SSHException, socket.error):
            return True
        except Exception:
            return False
        return False

    def node_terminated(self, settings, node_id):
        try:
            get_this_vm(node_id, settings)
            return False
        except Exception, e:
           return True

    def recorded_failed_node(self, failed_nodes, ip_address):
        if ip_address in [x[1] for x in failed_nodes if x[1] == ip_address]:
            return True
        return False


    def detect_failure(self, exception):
        logger.debug('exception is %s ' % exception.__class__)
        try:
            logger.debug(exception.__class__)
            raise exception.__class__
        except (AuthError, SSHException, socket.error):
            return True, 'ssh_failure'
        except Exception as e:
            return True, e
        return False, ''


