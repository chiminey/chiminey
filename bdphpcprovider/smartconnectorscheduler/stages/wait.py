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
import ast
import os
from bdphpcprovider.platform import manage
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import (models,
                                                    smartconnector)
from bdphpcprovider.reliabilityframework.ftmanager import FTManager
from bdphpcprovider.reliabilityframework.failuredetection import FailureDetection
from bdphpcprovider.sshconnection import open_connection

from bdphpcprovider import compute
from bdphpcprovider import messages
from bdphpcprovider import storage
from bdphpcprovider.runsettings import getval, setvals, setval, getvals, update, SettingNotFoundException


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Wait(Stage):
    """
        Return whether the run has finished or not
    """

    def __init__(self, user_settings=None):
        self.runs_left = 0
        self.error_nodes = 0
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        logger.debug("Wait stage initialised")

    def triggered(self, run_settings):
        """
            Checks whether there is a non-zero number of runs still going.
        """
        self.ftmanager = FTManager()
        self.failure_detector = FailureDetection()
        #self.cleanup_nodes = self.ftmanager.get_cleanup_nodes(run_settings, smartconnector)
        try:
            failed_str = getval(run_settings, '%s/stages/create/failed_nodes' % RMIT_SCHEMA)
            # failed_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'failed_nodes']

            self.failed_nodes = ast.literal_eval(failed_str)
        except SettingNotFoundException, e:
            logger.debug(e)
            self.failed_nodes = []
        except ValueError, e:
            logger.warn(e)
            self.failed_nodes = []

        try:
            executed_procs_str = getval(run_settings, '%s/stages/execute/executed_procs' % RMIT_SCHEMA)
            # executed_procs_str = run_settings['http://rmit.edu.au/schemas/stages/execute'][u'executed_procs']

            self.executed_procs = ast.literal_eval(executed_procs_str)
        except SettingNotFoundException, e:
            logger.debug(e)
            return False
        except ValueError, e:
            logger.error(e)
            return False

        try:
            self.all_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/all_processes' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.all_processes = []

        try:
            self.current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.current_processes = []

        try:
            self.exec_procs = ast.literal_eval(getval(run_settings, '%s/stages/schedule/executed_procs' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.exec_procs = []

        # self.all_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
        #         'http://rmit.edu.au/schemas/stages/schedule/all_processes'))

        # self.current_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
        #         'http://rmit.edu.au/schemas/stages/schedule/current_processes'))

        # self.exec_procs = ast.literal_eval(smartconnector.get_existing_key(run_settings,
        #         'http://rmit.edu.au/schemas/stages/execute/executed_procs'))

        if len(self.current_processes) == 0:
            return False

        executed_not_running = [x for x in self.current_processes if x['status'] == 'ready']
        if executed_not_running:
            logger.debug('executed_not_running=%s' % executed_not_running)
            return False
        else:
            logger.debug('No ready: executed_not_running=%s' % executed_not_running)

        try:
            reschedule_str = getval(run_settings, '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA)
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
            if self.procs_2b_rescheduled:
                return False
        except (ValueError, SettingNotFoundException) as e:
            logger.debug(e)
            self.procs_2b_rescheduled = []

        # try:
        #     reschedule_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'procs_2b_rescheduled']
        #     self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
        #     if self.procs_2b_rescheduled:
        #         return False
        # except KeyError, e:
        #     logger.debug(e)
        #     self.procs_2b_rescheduled = []

        try:
            self.reschedule_failed_procs = getval(run_settings, '%s/input/reliability/reschedule_failed_processes' % RMIT_SCHEMA)
        except SettingNotFoundException:
            self.reschedule_failed_procs = []  # FIXME: check this is correct
        # self.reschedule_failed_procs = run_settings['http://rmit.edu.au/schemas/input/reliability'][u'reschedule_failed_processes']

        self.failed_processes = self.ftmanager.\
                    get_total_failed_processes(self.executed_procs)

        logger.debug("self.failed_processes=%s" % self.failed_processes)
        # if we have no runs_left then we must have finished all the runs

        try:
            runs_left = getval(run_settings, '%s/stages/run/runs_left' % RMIT_SCHEMA)
        except SettingNotFoundException:
            pass
        else:
            logger.debug("runs_left=%s" % runs_left)
            created_str = getval(run_settings, '%s/stages/create/created_nodes' % RMIT_SCHEMA)
            self.created_nodes = ast.literal_eval(created_str)
            return runs_left

        # if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
        #     created_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'created_nodes']
        #     self.created_nodes = ast.literal_eval(created_str)
        #     return run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left']
        logger.debug("wait not triggered")
        return False

    def job_finished(self, ip_address, process_id, retry_left, settings):
        """
            Return True if package job on instance_id has job_finished
        """
        # TODO: maybe this should be a reusable library method?
        ip = ip_address
        logger.debug("ip=%s" % ip)
        curr_username = settings['username']
        settings['username'] = 'root'
        relative_path = settings['type'] + '@' + settings['payload_destination'] + "/" + process_id
        destination = smartconnector.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip)
        makefile_path = storage.get_make_path(destination)

        try:
            ssh = open_connection(ip_address=ip, settings=settings)
            (command_out, errs) = compute.run_make(ssh,
                                                   makefile_path,
                                                   "running")
        except Exception, e:
            # Failure detection and then management
            logger.debug('error is = %s' % e)
            process_failed = False
            node_failed = False
            if self.failure_detector.ssh_timed_out(e):
                node = [x for x in self.created_nodes if x[1] == ip_address]
                if self.failure_detector.node_terminated(settings, node[0][0]):
                    if not self.failure_detector.recorded_failed_node(
                            self.failed_nodes, ip_address):
                        self.failed_nodes.append(node[0])
                    node_failed = True
                else:
                    if not retry_left:
                        process_failed = True
                    else:
                        process_lists = [self.executed_procs, self.current_processes,
                                         self.all_processes]
                        self.ftmanager.decrease_max_retry(
                            process_lists, ip_address, process_id)
                # Failure management
                if node_failed or process_failed:
                    process_lists = [self.executed_procs,
                                     self.current_processes, self.all_processes]
                    if node_failed:
                        self.ftmanager.flag_all_processes(process_lists, ip_address)
                    elif process_failed:
                        self.ftmanager.flag_this_process(
                            process_lists, ip_address, process_id)
                    self.failed_processes = self.ftmanager.\
                        get_total_failed_processes(self.executed_procs)
                    if self.reschedule_failed_procs:
                        self.ftmanager.collect_failed_processes(
                            self.executed_procs, self.procs_2b_rescheduled)
            else:
                raise
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if "stopped" in line:
                    return True
        #return True  # FIXME: this may be undesirable
        return False

    def get_output(self, ip_address, process_id, output_dir, local_settings,
                   computation_platform_settings, output_storage_settings):
        """
            Retrieve the output from the task on the node
        """
        logger.debug("get_output of process %s on %s" % (process_id, ip_address))
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        cloud_path = os.path.join(local_settings['payload_destination'],
                                  process_id,
                                  local_settings['payload_cloud_dirname']
                                  )
        logger.debug("cloud_path=%s" % cloud_path)
        logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
        ip = ip_address  # botocloudconnector.get_instance_ip(instance_id, settings)
        #ssh = open_connection(ip_address=ip, settings=settings)
        source_files_location = "%s://%s@%s" % (computation_platform_settings['scheme'],
                                                computation_platform_settings['type'],
                                                 os.path.join(ip, cloud_path))
        source_files_url = smartconnector.get_url_with_pkey(
            computation_platform_settings, source_files_location,
            is_relative_path=False)
        logger.debug('source_files_url=%s' % source_files_url)

        dest_files_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
            output_prefix + os.path.join(
                self.job_dir, self.output_dir, process_id),
            is_relative_path=False)
        logger.debug('dest_files_url=%s' % dest_files_url)
        #hrmcstages.delete_files(dest_files_url, exceptions=[]) #FIXme: uncomment as needed
        # FIXME: might want to turn on paramiko compress function
        # to speed up this transfer
        storage.copy_directories(source_files_url, dest_files_url)

    def process(self, run_settings):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        def retrieve_local_settings(run_settings, local_settings):
            update(local_settings, run_settings,
                '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
                '%s/system/platform' % RMIT_SCHEMA,
                '%s/stages/run/payload_cloud_dirname' % RMIT_SCHEMA
                   )
            # smartconnector.copy_settings(local_settings, run_settings,
            #     'http://rmit.edu.au/schemas/stages/setup/payload_destination')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     'http://rmit.edu.au/schemas/system/platform')
            # smartconnector.copy_settings(local_settings, run_settings,
            #     'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')

            local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
            # local_settings['bdp_username'] = run_settings[
            #     RMIT_SCHEMA + '/bdp_userprofile']['username']

            logger.debug('retrieve completed')

        retrieve_local_settings(run_settings, local_settings)
        logger.debug("local_settings=%s" % local_settings)

        self.contextid = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)
        # self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
        # output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, local_settings['bdp_username'])
        # FIXME: Need to be consistent with how we handle settings here.  Prob combine all into
        # single local_settings for simplicity.
        output_storage_settings['bdp_username'] = local_settings['bdp_username']

        offset = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
        # offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        try:
            self.finished_nodes = getval(run_settings, '%s/stages/run/finished_nodes' % RMIT_SCHEMA)
            # self.finished_nodes = smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/stages/run/finished_nodes')
        except SettingNotFoundException:
            self.finished_nodes = '[]'

        try:
            self.id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
            # self.id = int(smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/system/id'))

            self.output_dir = "output_%s" % self.id
        except (SettingNotFoundException, ValueError):
            self.id = 0
            self.output_dir = "output"

        logger.debug("output_dir=%s" % self.output_dir)
        logger.debug("run_settings=%s" % run_settings)
        logger.debug("Wait stage process began")

        processes = self.executed_procs
        self.error_nodes = []
        # TODO: parse finished_nodes input
        logger.debug('self.finished_nodes=%s' % self.finished_nodes)
        self.finished_nodes = ast.literal_eval(self.finished_nodes)

        computation_platform_url = getval(run_settings, '%s/platform/computation/platform_url' % RMIT_SCHEMA)
        # computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
        comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
        local_settings.update(comp_pltf_settings)
        comp_pltf_settings['bdp_username'] = local_settings['bdp_username']

        for process in processes:
            #instance_id = node.id
            ip_address = process['ip_address']
            process_id = process['id']
            retry_left = process['retry_left']
            #ip = botocloudconnector.get_instance_ip(instance_id, self.boto_settings)
            #ssh = open_connection(ip_address=ip, settings=self.boto_settings)
            #if not botocloudconnector.is_vm_running(node):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                #FIXME: should error nodes be counted as finished?
            #    logging.error('Instance %s not running' % instance_id)
            #    self.error_nodes.append(node)
            #    continue
            fin = self.job_finished(ip_address, process_id, retry_left, local_settings)
            logger.debug("fin=%s" % fin)
            if fin:
                logger.debug("done. output is available")
                logger.debug("node=%s" % str(process))
                logger.debug("finished_nodes=%s" % self.finished_nodes)
                #FIXME: for multiple nodes, if one finishes before the other then
                #its output will be retrieved, but it may again when the other node fails, because
                #we cannot tell whether we have prevous retrieved this output before and finished_nodes
                # is not maintained between triggerings...
                if not (int(process_id) in [int(x['id'])
                                            for x in self.finished_nodes
                                            if int(process_id) == int(x['id'])]):
                    self.get_output(ip_address, process_id, self.output_dir,
                                    local_settings, comp_pltf_settings,
                                    output_storage_settings)

                    audit_url = smartconnector.get_url_with_pkey(
                        comp_pltf_settings, os.path.join(
                            self.output_dir, process_id, "audit.txt"),
                        is_relative_path=True)
                    fsys = storage.get_filesystem(audit_url)
                    logger.debug("Audit file url %s" % audit_url)
                    if fsys.exists(audit_url):
                        fsys.delete(audit_url)
                    self.finished_nodes.append(process)
                    logger.debug('finished_processes=%s' % self.finished_nodes)
                    for iterator, p in enumerate(self.all_processes):
                        if int(p['id']) == int(process_id) and p['status'] == 'running':
                            self.all_processes[iterator]['status'] = 'completed'
                    for iterator, p in enumerate(self.executed_procs):
                        if int(p['id']) == int(process_id) and p['status'] == 'running':
                            self.executed_procs[iterator]['status'] = 'completed'
                    for iterator, p in enumerate(self.current_processes):
                        if int(p['id']) == int(process_id) and p['status'] == 'running':
                            self.current_processes[iterator]['status'] = 'completed'
                    messages.info(run_settings, "%s: waiting (%s process left)" % (
                        self.id + 1, len(self.executed_procs) - (len(self.finished_nodes) + self.failed_processes)))
                else:
                    logger.warn("We have already "
                        + "processed output of %s on node %s" % (process_id, ip_address))
            else:
                print "job %s at %s not completed" % (process_id, ip_address)

    def output(self, run_settings):
        """
        Output new runs_left value (including zero value)
        """
        logger.debug("finished stage output")
        nodes_working = len(self.executed_procs) - (len(self.finished_nodes) + self.failed_processes)
        #if len(self.finished_nodes) == 0 and self.failed_processes == 0:
        #    nodes_working = 0
        logger.debug("%d %d " % (len(self.finished_nodes), self.failed_processes))
        logger.debug("self.executed_procs=%s" % self.executed_procs)
        logger.debug("self.finished_nodes=%s" % self.finished_nodes)

        #FIXME: nodes_working can be negative

        # FIXME: possible race condition?
        # if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
        #     run_settings['http://rmit.edu.au/schemas/stages/run'] = {}
        # #run_settings['http://rmit.edu.au/schemas/stages/run']['runs_left'] = nodes_working
        #run_settings['http://rmit.edu.au/schemas/stages/run']['error_nodes'] = nodes_working

        setvals(run_settings, {
                '%s/stages/run/runs_left' % RMIT_SCHEMA: nodes_working,
                '%s/stages/run/error_nodes' % RMIT_SCHEMA: nodes_working,
                })

        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/run',
        #     {})[u'runs_left'] = nodes_working

        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/run',
        #     {})[u'error_nodes'] = nodes_working

        if not nodes_working:
            self.finished_nodes = []
        #run_settings['http://rmit.edu.au/schemas/stages/run']['finished_nodes'] = str(self.finished_nodes)

        setvals(run_settings, {
                '%s/stages/run/finished_nodes' % RMIT_SCHEMA: str(self.finished_nodes),
                '%s/stages/schedule/all_processes' % RMIT_SCHEMA: str(self.all_processes),
                '%s/stages/schedule/current_processes' % RMIT_SCHEMA: str(self.current_processes),
                '%s/stages/execute/executed_procs' % RMIT_SCHEMA: str(self.executed_procs)
                })
        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/run',
        #     {})[u'finished_nodes'] = str(self.finished_nodes)

        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/schedule',
        #     {})[u'all_processes'] = str(self.all_processes)
        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/schedule',
        #     {})[u'current_processes'] = str(self.current_processes)

        # run_settings.setdefault(
        #     'http://rmit.edu.au/schemas/stages/execute',
        #     {})[u'executed_procs'] = str(self.executed_procs)

        # if self.cleanup_nodes:
        #    run_settings.setdefault(
        #    'http://rmit.edu.au/schemas/reliability', {})[u'cleanup_nodes'] = self.cleanup_nodes

        if self.failed_nodes:
            setval(run_settings, '%s/stages/create/failed_nodes' % RMIT_SCHEMA, self.failed_nodes)
            # run_settings.setdefault(
            # 'http://rmit.edu.au/schemas/stages/create', {})[u'failed_nodes'] = self.failed_nodes

        completed_procs = [x for x in self.executed_procs if x['status'] == 'completed']
        messages.info(run_settings, "%s: waiting (%s of %s processes done)"
            % (self.id + 1, len(completed_procs), len(self.current_processes)))

        if self.procs_2b_rescheduled:
            setvals(run_settings, {
                    '%s/stages/schedule/scheduled_started' % RMIT_SCHEMA: 0,
                    '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA: self.procs_2b_rescheduled
                    })
            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #     {})[u'schedule_started'] = 0
            # run_settings.setdefault(
            #         'http://rmit.edu.au/schemas/stages/schedule',
            #         {})[u'procs_2b_rescheduled'] = self.procs_2b_rescheduled
        return run_settings


