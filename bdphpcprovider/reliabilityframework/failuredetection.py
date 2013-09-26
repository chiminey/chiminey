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

from bdphpcprovider.reliabilityframework.ftmanager import FTManager
from bdphpcprovider.smartconnectorscheduler import botocloudconnector

logger = logging.getLogger(__name__)


class FailureDetection(FTManager):
    def sufficient_vms(self, created_vms, min_number_vms):
        if int(created_vms) < int(min_number_vms):
            logger.error('Insufficient no. VMs created')
            logger.info('created_nodes=%d but minimmum_requirement=%d'
                        % (created_vms, min_number_vms))
            return False
        return True

    def ssh_timed_out(self, error_message):
        if 'Connection timed out' in error_message:
            return True
        if 'No route to host' in error_message:
            return True
        return False

    def node_terminated(self, settings, node_id):
        node = botocloudconnector.get_this_instance(node_id, settings)
        if not node:
            return True
        return False

    def recorded_failed_node(self, failed_nodes, ip_address):
        if ip_address in [x[1] for x in failed_nodes if x[1] == ip_address]:
            return True
        return False





