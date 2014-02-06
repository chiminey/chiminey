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

from bdphpcprovider.corestages.strategies.strategy import Strategy
from bdphpcprovider.cloudconnection import create_vms, print_vms
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientVMError
from bdphpcprovider.reliabilityframework import FTManager
from bdphpcprovider import messages


class CloudStrategy(Strategy):
    def create_resource(self, connection_settings, platform_settings, context_id):
        created_nodes = []
        group_id, vms_detail_list = create_vms(connection_settings)

        try:
            if not vms_detail_list or len(vms_detail_list) < connection_settings['min_count']:
                raise InsufficientVMError
            print_vms(connection_settings, all_vms=vms_detail_list)
            for vm in vms_detail_list:
                if not vm.ip_address:
                    vm.ip_address = vm.private_ip_address
            created_nodes = [[x.id, x.ip_address, unicode(x.region), 'running'] for x in vms_detail_list]
            messages.info_context(context_id, "1: create (%s nodes created)" % len(vms_detail_list))
        except InsufficientVMError as e:
            group_id = 'UNKNOWN'
            messages.error_context(context_id, "error: sufficient VMs cannot be created")
            ftmanager = FTManager()
            ftmanager.manage_failure(
                e, settings=platform_settings,
                created_vms=vms_detail_list)
        return group_id, created_nodes