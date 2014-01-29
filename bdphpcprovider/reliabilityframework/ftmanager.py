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
from bdphpcprovider.reliabilityframework.failuredetection import FailureDetection
from bdphpcprovider.cloudconnection import get_this_vm
logger = logging.getLogger(__name__)


class FTManager():
    def collect_failed_processes(self, source):
        destination = []
        for iterator, process in enumerate(source):
            if process['status'] == 'failed':
                destination.append(process)
        return destination

    def flag_all_processes(self, process_lists, ip_address):
        for process_list in process_lists:
            for process in process_list:
                if process['ip_address'] == ip_address \
                    and process['status'] == 'running':
                    process['status'] = 'failed'

    def flag_this_process(self, process_lists, ip_address, process_id):
        for process_list in process_lists:
            for process in process_list:
                if process['ip_address'] == ip_address \
                    and process['status'] == 'running' \
                    and process['id'] == process_id:
                    process['status'] = 'failed'

    def get_total_failed_processes(self, process_list):
        no_failed_procs = 0
        for process in process_list:
            if process['status'] == 'failed':
                no_failed_procs += 1
        return no_failed_procs

    def decrease_max_retry(self, process_lists, ip_address, process_id):
        for process_list in process_lists:
            for process in process_list:
                if process['ip_address'] == ip_address \
                    and process['id'] == process_id:
                    retry = int(process['retry_left'])
                    if retry > 0:
                        process['retry_left'] = retry - 1

    def manage_failed_process(self, settings, process_id, host_node, host_node_id,
                              host_node_ip, failed_nodes, executed_procs, current_procs, all_procs):
        failure_detection = FailureDetection()
        list_of_process_lists = [executed_procs, current_procs, all_procs]
        if failure_detection.node_terminated(settings, host_node_id):
            if not failure_detection.recorded_failed_node(
                            failed_nodes, host_node_ip):
                failed_nodes.append(host_node)
            self.flag_all_processes(list_of_process_lists, host_node_ip)
        else:
            self.decrease_max_retry(list_of_process_lists, host_node_ip, process_id)
            self.flag_this_process(list_of_process_lists, host_node_ip, process_id)
        failed_processes = self.get_total_failed_processes(current_procs)
        procs_2b_rescheduled = self.collect_failed_processes(current_procs)
        return failed_processes, procs_2b_rescheduled



































































