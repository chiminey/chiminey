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
import os
from chiminey.sshconnection import open_connection
from chiminey.storage import get_url_with_credentials
from chiminey.storage import get_make_path
from chiminey.compute import run_make
from chiminey.corestages.strategies.strategy import Strategy


logger = logging.getLogger(__name__)
RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class AsynchronousWaitStrategy(Strategy):
    def is_job_finished(self, wait_class, ip_address, process_id, retry_left, settings, relative_path_suffix):
        """
            Return True if package job on instance_id has is_job_finished
        """
        # TODO: maybe this should be a reusable library method?
        ip = ip_address
        logger.debug("ip=%s" % ip)
        curr_username = settings['username']
        # settings['username'] = 'root'
        #relative_path = settings['type'] + '@' + settings['payload_destination'] + "/" + process_id
        relative_path = settings['type'] + '@' + os.path.join(relative_path_suffix, process_id)
        destination = get_url_with_credentials(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip)
        makefile_path = get_make_path(destination)
        ssh = None
        try:
            logger.debug('trying ssh')
            ssh = open_connection(ip_address=ip, settings=settings)
            logger.debug('successful ssh')
            (command_out, errs) = run_make(ssh, makefile_path, "process_running_done")
            ssh.close()
            logger.debug("command_out2=(%s, %s)" % (command_out, errs))
            if command_out:
                logger.debug("command_out = %s" % command_out)
                for line in command_out:
                    if "stopped" in line:
                        return True
        except Exception, e:

            # Failure detection and then management
            logger.debug('error is = %s' % e)
            process_failed = False
            node_failed = False
            logger.debug('Is there error? %s' % wait_class.failure_detector.failed_ssh_connection(e))
            if wait_class.failure_detector.failed_ssh_connection(e):
                node = [x for x in wait_class.created_nodes if x[1] == ip_address]
                wait_class.failed_processes = wait_class.ftmanager.manage_failed_process(
                    settings, process_id, node[0], node[0][0], ip_address,
                    wait_class.failed_nodes, wait_class.executed_procs, wait_class.current_processes,
                    wait_class.all_processes, wait_class.procs_2b_rescheduled)
                #wait_class.procs_2b_rescheduled.extend(rescheduled_prcs)
                '''
                if wait_class.failure_detector.node_terminated(settings, node[0][0]):
                    if not wait_class.failure_detector.recorded_failed_node(
                            wait_class.failed_nodes, ip_address):
                        wait_class.failed_nodes.append(node[0])
                    node_failed = True
                else:
                    if not retry_left:
                        process_failed = True
                    else:
                        process_lists = [wait_class.executed_procs, wait_class.current_processes,
                                         wait_class.all_processes]
                        wait_class.ftmanager.decrease_max_retry(
                            process_lists, ip_address, process_id)
                # Failure management
                if node_failed or process_failed:
                    process_lists = [wait_class.executed_procs,
                                     wait_class.current_processes, wait_class.all_processes]
                    if node_failed:
                        wait_class.ftmanager.flag_all_processes(process_lists, ip_address)
                    elif process_failed:
                        wait_class.ftmanager.flag_this_process(
                            process_lists, ip_address, process_id)
                    wait_class.failed_processes = wait_class.ftmanager.\
                        get_total_failed_processes(wait_class.executed_procs)
                    if wait_class.reschedule_failed_procs:
                        wait_class.ftmanager.collect_failed_processes(
                            wait_class.executed_procs, wait_class.procs_2b_rescheduled)

                '''
            else:
                raise
        finally:
            if ssh:
                ssh.close()
        return False