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
from bdphpcprovider.corestages.strategies.strategy import Strategy
from bdphpcprovider.cloudconnection import create_vms, destroy_vms, print_vms, get_registered_vms
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientVMError
from bdphpcprovider.reliabilityframework import FTManager
from bdphpcprovider import messages
from bdphpcprovider.runsettings import SettingNotFoundException, getval, update
from bdphpcprovider.corestages.strategies import cloudschedulestrategy as schedule
from bdphpcprovider.corestages.strategies import cloudbootstrapstrategy as bootstrap

logger = logging.getLogger(__name__)
RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class CloudStrategy(Strategy):
    def set_create_settings(self, run_settings, local_settings):
        update(local_settings, run_settings, '%s/stages/create/vm_image' % RMIT_SCHEMA,
               '%s/stages/create/cloud_sleep_interval' % RMIT_SCHEMA,
               '%s/system/contextid' % RMIT_SCHEMA
               )
        try:
            local_settings['min_count'] = int(getval(
                run_settings, '%s/input/system/cloud/minimum_number_vm_instances' % RMIT_SCHEMA))
        except SettingNotFoundException:
            local_settings['min_count'] = 1
        try:
            local_settings['max_count'] = int(getval(
                run_settings, '%s/input/system/cloud/number_vm_instances' % RMIT_SCHEMA))
        except SettingNotFoundException:
            local_settings['max_count'] = 1

    def create_resource(self, local_settings):
        created_nodes = []
        group_id, vms_detail_list = create_vms(local_settings)
        try:
            if not vms_detail_list or len(vms_detail_list) < local_settings['min_count']:
                raise InsufficientVMError
            print_vms(local_settings, all_vms=vms_detail_list)
            for vm in vms_detail_list:
                if not vm.ip_address:
                    vm.ip_address = vm.private_ip_address
            created_nodes = [[x.id, x.ip_address, unicode(x.region), 'running'] for x in vms_detail_list]
            messages.info_context(int(local_settings['contextid']),
                                  "1: create (%s nodes created)" % len(vms_detail_list))
        except InsufficientVMError as e:
            group_id = 'UNKNOWN'
            messages.error_context(int(local_settings['contextid']),
                                   "error: sufficient VMs cannot be created")
            ftmanager = FTManager()
            ftmanager.manage_failure(
                e, settings=local_settings,
                created_vms=vms_detail_list)
        return group_id, created_nodes

    def set_bootstrap_settings(self, run_settings, local_settings):
        bootstrap.set_bootstrap_settings(run_settings, local_settings)

    def start_multi_bootstrap_task(self, settings):
        bootstrap.start_multi_bootstrap_task(settings)

    def complete_bootstrap(self, bootstrap_class, local_settings):
        bootstrap.complete_bootstrap(bootstrap_class, local_settings)

    def set_schedule_settings(self, run_settings, local_settings):
        schedule.set_schedule_settings(run_settings, local_settings)

    def start_schedule_task(self, schedule_class, run_settings, local_settings):
        schedule_class.nodes = get_registered_vms(
                local_settings, node_type='bootstrapped_nodes')
        schedule.schedule_task(schedule_class, run_settings, local_settings)

    def complete_schedule(self, schedule_class, local_settings):
        schedule.complete_schedule(schedule_class, local_settings)

    def set_destroy_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
               #'%s/system/platform' % RMIT_SCHEMA,
               '%s/stages/create/cloud_sleep_interval' % RMIT_SCHEMA,
               '%s/system/contextid' % RMIT_SCHEMA,
               )
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

    def destroy_resource(self, run_settings, local_settings):
        node_type = []
        try:
            created_nodes = getval(run_settings, '%s/stages/create' % RMIT_SCHEMA)
            node_type.append('created_nodes')
        except SettingNotFoundException:
            pass
        if node_type:
            destroy_vms(local_settings, node_types=node_type)














