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
import socket
from chiminey.reliabilityframework.failuredetection import FailureDetection
from chiminey.cloudconnection import get_this_vm
from chiminey.sshconnection import AuthError, SSHException
from chiminey.smartconnectorscheduler.stages.errors import \
    InsufficientVMError, NoRegisteredVMError, VMTerminatedError
from chiminey.cloudconnection import destroy_vms, get_registered_vms


logger = logging.getLogger(__name__)


class FTManager():
    def __init__(self, **kwargs):
        try:
            self.stage_class = kwargs['stage_class']
        except KeyError:
            self.stage_class = None

    def collect_failed_processes(self, source, destination):
        for iterator, process in enumerate(source):
            if process['status'] == 'failed' and \
                    process not in destination:
                destination.append(process)

    def _flag_failed_vm(self, vm_ip, all_vms):
        for vm in all_vms:
            if str(vm[1]) == str(vm_ip):
                vm[3] = 'failed'
                break

    def _flag_all_failed_vms(self, all_vms):
        for vm in all_vms:
            vm[3] = 'failed'


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
                if str(process['ip_address']) is str(ip_address) \
                    and process['id'] == process_id:
                    retry = int(process['retry_left'])
                    if retry > 0:
                        process['retry_left'] = retry - 1

    def manage_failed_process(self, settings, process_id, host_node, host_node_id,
                              host_node_ip, failed_nodes, executed_procs, current_procs, all_procs,
                              procs_2b_rescheduled):
        failure_detection = FailureDetection()
        list_of_process_lists = [executed_procs, current_procs, all_procs]
        self.decrease_max_retry(list_of_process_lists, host_node_ip, process_id)
        if failure_detection.node_terminated(settings, host_node_id):
            if not failure_detection.recorded_failed_node(
                            failed_nodes, host_node_ip):
                failed_nodes.append(host_node)
            self.flag_all_processes(list_of_process_lists, host_node_ip)
        else:
            self.flag_this_process(list_of_process_lists, host_node_ip, process_id)
        failed_processes = self.get_total_failed_processes(current_procs)
        self.collect_failed_processes(current_procs, procs_2b_rescheduled)
        return failed_processes


    def manage_failure(self, exception, **kwargs):
        logger.debug('exception is %s ' % exception.__class__)
        try:
            raise exception.__class__
        except (AuthError, SSHException, socket.error):
            logger.debug('ssh failure detected')
            self._manage_ssh_failure(kwargs)
        except InsufficientVMError:
            logger.debug('insufficient VM error detected')
            self._manage_insufficient_vm_error(kwargs)
        except NoRegisteredVMError:
            logger.debug('NoRegisteredVMError detected')
            self._manage_no_registered_vm_error(kwargs)
        except VMTerminatedError:
            logger.debug('VMTerminatedError detected')
            self._manage_vm_terminated_error(kwargs)

    def _manage_vm_terminated_error(self, kwargs):
        try:
            self.stage_class = kwargs['stage_class']
            running_vms = get_registered_vms(kwargs['settings'])
            running_vms_id = []
            for vm in running_vms:
                running_vms_id.append(vm.id)
            created_vms = self.stage_class.created_nodes
            for vm in created_vms:
                if str(vm[0]) not in running_vms_id:
                    vm[3] = 'failed'
        except KeyError as e:
            logger.debug('key_error = %s' % e)

    #stage_class
    def _manage_ssh_failure(self, kwargs):
        try:
            self.stage_class = kwargs['stage_class']
            failure_detection = FailureDetection()
            vm_terminated = failure_detection.node_terminated(
                kwargs['settings'], kwargs['vm_id'])
            if vm_terminated:
                self._flag_failed_vm(kwargs['vm_ip'], self.stage_class.created_nodes)
                list_of_process_lists = [self.stage_class.current_procs, self.stage_class.all_procs]
                self.flag_all_processes(list_of_process_lists, kwargs['vm_ip'])
                self.decrease_max_retry(list_of_process_lists, kwargs['vm_ip'], kwargs['process_id'])
            else:
                self._manage_process_terminated_error(kwargs)
        except KeyError as e:
            logger.debug('key_error=%s' % e)

    def _manage_vm_terminated_error2(self, kwargs):
        try:
            self._flag_failed_vm(kwargs['vm_ip'], self.stage_class.created_nodes)
            list_of_process_lists = [self.stage_class.current_procs, self.stage_class.all_procs]
            self.flag_all_processes(list_of_process_lists, kwargs['vm_ip'])
            self.decrease_max_retry(list_of_process_lists, kwargs['vm_ip'], kwargs['process_id'])
        except KeyError as e:
            logger.debug('key_error=%s' % e)

    def _manage_process_terminated_error(self, kwargs):
        pass


    def _manage_insufficient_vm_error(self, kwargs):
        try:
            logger.info("Sufficient number VMs cannot be created for this computation."
                        "Increase your quota or decrease your minimum requirement")
            destroy_vms(kwargs['settings'], registered_vms=kwargs['created_vms'])
        except KeyError:
            pass

    def _manage_no_registered_vm_error(self, kwargs):
        logger.debug('managing NoRegisteredVMError')
        try:
            self.stage_class = kwargs['stage_class']
            self._flag_all_failed_vms(self.stage_class.created_nodes)
            logger.debug('NoRegisteredVMError managed %s' % self.stage_class.created_nodes)
        except KeyError as e:
            logger.debug('key_error=%s' % e)

































































