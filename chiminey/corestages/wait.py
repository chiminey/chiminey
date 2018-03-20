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
import datetime
import json

from chiminey.platform import get_platform_settings, get_job_dir
from chiminey.corestages import stage
from chiminey.corestages.stage import Stage
from chiminey.smartconnectorscheduler import models
from chiminey.reliabilityframework.ftmanager import FTManager
from chiminey.corestages import strategies
from chiminey.reliabilityframework.failuredetection import FailureDetection
from chiminey import messages
from chiminey import storage

from chiminey.runsettings import getval, setvals, setval, getvals, SettingNotFoundException
from chiminey.storage import get_url_with_credentials
from chiminey.corestages import timings

logger = logging.getLogger(__name__)
from django.conf import settings as django_settings


class Wait(Stage):
    """
        Return whether the run has finished or not
    """

    def __init__(self, user_settings=None):
        self.runs_left = 0
        self.error_nodes = 0
        self.output_transfer_total_time = timings.timedelta_initiate()
        logger.debug("Wait stage initialised")

    def is_triggered(self, run_settings):
        """
            Checks whether there is a non-zero number of runs still going.
        """

        self.ftmanager = FTManager()
        self.failure_detector = FailureDetection()
        #self.cleanup_nodes = self.ftmanager.get_cleanup_nodes(run_settings, smartconnectorscheduler)
        try:
            failed_str = getval(run_settings, '%s/stages/create/failed_nodes' % django_settings.SCHEMA_PREFIX)
            self.failed_nodes = ast.literal_eval(failed_str)
        except SettingNotFoundException, e:
            logger.debug(e)
            self.failed_nodes = []
        except ValueError, e:
            logger.warn(e)
            self.failed_nodes = []

        #todo: remove executed try ... except
        try:
            executed_procs_str = getval(run_settings, '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX)
            self.executed_procs = ast.literal_eval(executed_procs_str)
        except SettingNotFoundException, e:
            logger.debug(e)
            return False
        except ValueError, e:
            logger.error(e)
            return False

        try:
            self.all_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.all_processes = []

        try:
            self.current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.current_processes = []


        try:
            self.exec_procs = ast.literal_eval(getval(run_settings, '%s/stages/schedule/executed_procs' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.exec_procs = []

        if len(self.current_processes) == 0:
            return False

        executed_not_running = [x for x in self.current_processes if x['status'] == 'ready']
        if executed_not_running:
            logger.debug('executed_not_running=%s' % executed_not_running)
            return False
        else:
            logger.debug('No ready: executed_not_running=%s' % executed_not_running)

        try:
            reschedule_str = getval(run_settings, '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX)
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
            if self.procs_2b_rescheduled:
                return False
        except (ValueError, SettingNotFoundException) as e:
            logger.debug(e)
            self.procs_2b_rescheduled = []

        try:
            self.reschedule_failed_procs = getval(run_settings, '%s/input/reliability/reschedule_failed_processes' % django_settings.SCHEMA_PREFIX)
            created_str = getval(run_settings, '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX)
            self.created_nodes = ast.literal_eval(created_str)
        except SettingNotFoundException:
            self.reschedule_failed_procs = 0
            self.created_nodes = {}

        self.failed_processes = self.ftmanager.\
                    get_total_failed_processes(self.current_processes)  # self.executed_procs)

        logger.debug("self.failed_processes=%s" % self.failed_processes)
        # if we have no runs_left then we must have finished all the runs


        try:
            #runs_left = getval(run_settings, '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX)
            return getval(run_settings, '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            pass
        logger.debug("wait not triggered")
        return False

    '''
    def is_job_finished(self, ip_address, process_id, retry_left, settings):
        return True
    '''

    def get_output(self, ip_address, process_id, output_dir, local_settings,
                   computation_platform_settings, output_storage_settings,
                   run_settings):
        """
            Retrieve the output from the task on the node
        """

        logger.debug("get_output of process %s on %s" % (process_id, ip_address))
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        #fixme: add call get_process_output_path
        #cloud_path = os.path.join(local_settings['payload_destination'],
        #                          #str(contextid), #fixme: uncomment
        #                          str(process_id),
        #                          local_settings['process_output_dirname']
        #                          )
        relative_path_suffix = self.get_relative_output_path(local_settings)
        cloud_path = os.path.join(relative_path_suffix,
                                  str(process_id),
                                  local_settings['process_output_dirname']
                                  )
        #cloud_path = self.get_process_output_path(run_settings, process_id)
        logger.debug("cloud_path=%s" % cloud_path)
        logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
        ip = ip_address  # botocloudconnector.get_instance_ip(instance_id, settings)
        #ssh = open_connection(ip_address=ip, settings=settings)
        source_files_location = "%s://%s@%s" % (computation_platform_settings['scheme'],
                                                computation_platform_settings['type'],
                                                 os.path.join(ip, cloud_path))
        source_files_url = get_url_with_credentials(
            computation_platform_settings, source_files_location,
            is_relative_path=False)
        logger.debug('source_files_url=%s' % source_files_url)

        dest_files_url = get_url_with_credentials(
            output_storage_settings,
            output_prefix + os.path.join(
                self.job_dir, self.output_dir, process_id),
            is_relative_path=False)
        logger.debug('dest_files_url=%s' % dest_files_url)
        # FIXME: might want to turn on paramiko compress function
        # to speed up this transfer
        storage.copy_directories(source_files_url, dest_files_url)


        #copying values file
        values_file_path = os.path.join(relative_path_suffix,
                                  str(process_id),
                                  local_settings['smart_connector_input'],
                                  django_settings.VALUES_FNAME
                                  )
        values_files_location = "%s://%s@%s" % (computation_platform_settings['scheme'],
                                                computation_platform_settings['type'],
                                                 os.path.join(ip, values_file_path))
        logger.debug("values_files_location=%s" % values_files_location)
        values_source_url = get_url_with_credentials(
        computation_platform_settings, values_files_location,
        is_relative_path=False)

        logger.debug("values_source_url=%s" % values_source_url)

        values_dest_url = get_url_with_credentials(
            output_storage_settings,
            output_prefix + os.path.join(
                self.job_dir, self.output_dir, process_id, django_settings.VALUES_FNAME),
            is_relative_path=False)
        logger.debug("values_dest_url=%s" % values_dest_url)
        try:
	    logger.debug('reading %s' % values_source_url)
            content = storage.get_file(values_source_url)
        except IOError, e:
            content = {}
        logger.debug('content=%s' % content)
        storage.put_file(values_dest_url, content)

        #reading timedata.txt file
        timedata_files_location = "%s://%s@%s" % (computation_platform_settings['scheme'],
                                                  computation_platform_settings['type'],
                                                  os.path.join(ip, cloud_path,"timedata.txt"))

        logger.debug("timedata_files_location=%s" % timedata_files_location)

        timedata_source_url = get_url_with_credentials(
                                                  computation_platform_settings, timedata_files_location,
                                                  is_relative_path=False)
        timedict={}
        try:
	    logger.debug('Reading %s' % timedata_source_url)
            content = storage.get_file(timedata_source_url)
            timedict = dict(ast.literal_eval(content))
            logger.debug("Timedata exec_start_time:%s" % timedict['exec_start_time'])
        except IOError, e:
            content = {}
        logger.debug('timedata.txt content=%s' % content)
        
        return timedict

    def process(self, run_settings):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """

        try:
            self.wait_stage_start_time = str(getval(run_settings, '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.wait_stage_start_time = timings.datetime_now_seconds()
        except ValueError, e:
            logger.error(e)


        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        retrieve_local_settings(run_settings, local_settings)
        logger.debug("local_settings=%s" % local_settings)

        self.contextid = getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)
        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % django_settings.SCHEMA_PREFIX)
        output_storage_settings = get_platform_settings(output_storage_url, local_settings['bdp_username'])
        # FIXME: Need to be consistent with how we handle settings here.  Prob combine all into
        # single local_settings for simplicity.
        output_storage_settings['bdp_username'] = local_settings['bdp_username']
        offset = getval(run_settings, '%s/platform/storage/output/offset' % django_settings.SCHEMA_PREFIX)
        self.job_dir = get_job_dir(output_storage_settings, offset)

        try:
            self.finished_nodes = getval(run_settings, '%s/stages/run/finished_nodes' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            self.finished_nodes = '[]'

        try:
            self.id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
            self.output_dir = "output_%s" % self.id
        except (SettingNotFoundException, ValueError):
            self.id = 0
            self.output_dir = "output"

        logger.debug("output_dir=%s" % self.output_dir)
        logger.debug("run_settings=%s" % run_settings)
        logger.debug("Wait stage process began")

        #processes = self.executed_procs
        processes = [x for x in self.current_processes if x['status'] == 'running']
        self.error_nodes = []
        # TODO: parse finished_nodes input
        logger.debug('self.finished_nodes=%s' % self.finished_nodes)
        self.finished_nodes = ast.literal_eval(self.finished_nodes)

        computation_platform_url = getval(run_settings, '%s/platform/computation/platform_url' % django_settings.SCHEMA_PREFIX)
        comp_pltf_settings = get_platform_settings(computation_platform_url, local_settings['bdp_username'])
        local_settings.update(comp_pltf_settings)
        comp_pltf_settings['bdp_username'] = local_settings['bdp_username']

        wait_strategy = strategies.SynchronousWaitStrategy()
        try:
            payload_source = getval(run_settings, '%s/stages/setup/payload_source' % django_settings.SCHEMA_PREFIX)
            if payload_source:
                wait_strategy = strategies.AsynchronousWaitStrategy()
        except SettingNotFoundException:
            pass

        self.output_transfer_begin = 0
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
            relative_path_suffix = self.get_relative_output_path(local_settings)
            fin = wait_strategy.is_job_finished( self,
                ip_address, process_id, retry_left,
                local_settings, relative_path_suffix)
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

                    for iterator, p in enumerate(self.current_processes):
                       if int(p['id']) == int(process_id):
                           out_trans_start_time = self.current_processes[iterator]['output_transfer_start_time'] = timings.datetime_now_milliseconds()
                           if not self.output_transfer_begin:
                               self.output_transfer_start_time = out_trans_start_time[:-4]
                               self.output_transfer_begin = 1
                    #timedata = self.get_output(ip_address, process_id, self.output_dir,
                    #                  local_settings, comp_pltf_settings,
                    #                  output_storage_settings, run_settings)
                    #for iterator, p in enumerate(self.current_processes):
                    #   if int(p['id']) == int(process_id):
                           timedata = self.get_output(ip_address, process_id, self.output_dir,
                                      local_settings, comp_pltf_settings,
                                      output_storage_settings, run_settings)

                           out_trans_end_time = self.current_processes[iterator]['output_transfer_end_time'] =  timings.datetime_now_milliseconds() 
                           self.output_transfer_end_time = out_trans_end_time[:-4] 

                           self.output_transfer_total_time = self.output_transfer_total_time + timings.microseconds_timedelta(out_trans_end_time, out_trans_start_time)

                           self.current_processes[iterator]['output_transfer_total_time'] = timings.timedelta_milliseconds(
                                          self.current_processes[iterator]['output_transfer_end_time'], 
                                          self.current_processes[iterator]['output_transfer_start_time']) 

                           self.current_processes[iterator]['varinp_transfer_total_time'] = timings.timedelta_milliseconds(
                                          self.current_processes[iterator]['varinp_transfer_end_time'], 
                                          self.current_processes[iterator]['varinp_transfer_start_time'])
                                          
                           if timedata:
                               self.current_processes[iterator]['sched_start_time'] = timedata['sched_start_time']
                               self.current_processes[iterator]['sched_end_time'] = timedata['sched_end_time']
                               self.current_processes[iterator]['sched_total_time'] = timings.timedelta_milliseconds(
                                          self.current_processes[iterator]['sched_end_time'], 
                                          self.current_processes[iterator]['sched_start_time'])
                                   
                               self.current_processes[iterator]['exec_start_time'] = timedata['exec_start_time']
                               self.current_processes[iterator]['exec_end_time'] = timedata['exec_end_time']
                               self.current_processes[iterator]['exec_total_time'] = timings.timedelta_milliseconds(
                                          self.current_processes[iterator]['exec_end_time'], 
                                          self.current_processes[iterator]['exec_start_time'])

                    audit_url = get_url_with_credentials(
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
                            #self.output_transfer_end_time = timings.datetime_now_seconds()
                            #self.output_transfer_total_time = self.output_transfer_total_time + timings.timedelta_seconds(self.output_transfer_end_time, self.output_transfer_start_time)
                else:
                    logger.warn("We have already "
                        + "processed output of %s on node %s" % (process_id, ip_address))
            else:
                print "job %s at %s not completed" % (process_id, ip_address)
            failed_processes = [x for x in self.current_processes if x['status'] == 'failed']
            logger.debug('failed_processes=%s' % failed_processes)
            logger.debug('failed_processes=%d' % len(failed_processes))
            messages.info(run_settings, "%d: Waiting %d processes (%d completed, %d failed) " % (
                self.id + 1, len(self.current_processes),  len(self.finished_nodes),
                len(failed_processes)))
        #try:
        #    self.current_processes_file = str(getval(run_settings, '%s/stages/schedule/current_processes_file' % django_settings.SCHEMA_PREFIX))
        #    timings.update_timings_dump(self.current_processes_file, self.current_processes)
        #except SettingNotFoundException:
        #    self.current_processes_file =''
        #except ValueError, e:
        #    logger.error(e)
        #try:
        #    self.all_processes_file = str(getval(run_settings, '%s/stages/schedule/all_processes_file' % django_settings.SCHEMA_PREFIX))
        #    timings.update_timings_dump(self.all_processes_file, self.all_processes)
        #except SettingNotFoundException:
        #    self.all_processes_file=''
        #except ValueError, e:
        #    logger.error(e)

    def output(self, run_settings):
        """
        Output new runs_left value (including zero value)
        """
        wait_stage_end_time = timings.datetime_now_seconds()
        wait_stage_total_time = timings.timedelta_seconds(wait_stage_end_time, self.wait_stage_start_time)
        logger.debug("finished stage output")

        executing_procs = [x for x in self.current_processes if x['status'] != 'ready']
        #nodes_working = len(self.executed_procs) - (len(self.finished_nodes) + self.failed_processes)
        nodes_working = len(executing_procs) - (len(self.finished_nodes) + self.failed_processes)



        #if len(self.finished_nodes) == 0 and self.failed_processes == 0:
        #    nodes_working = 0
        logger.debug("%d %d " %(len(self.finished_nodes), self.failed_processes))
        #logger.debug("self.executed_procs=%s" % self.executed_procs)
        logger.debug("self.executed_procs=%s" % executing_procs)
        logger.debug("self.finished_nodes=%s" % self.finished_nodes)

        #FIXME: nodes_working can be negative

        # FIXME: possible race condition?
        # if not self._exists(run_settings, '%s/stages/run' % django_settings.SCHEMA_PREFIX):
        #     run_settings['%s/stages/run' % django_settings.SCHEMA_PREFIX] = {}
        # #run_settings['%s/stages/run' % django_settings.SCHEMA_PREFIX]['runs_left'] = nodes_working
        #run_settings['%s/stages/run' % django_settings.SCHEMA_PREFIX]['error_nodes'] = nodes_working

        setvals(run_settings, {
                '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX: nodes_working,
                '%s/stages/run/error_nodes' % django_settings.SCHEMA_PREFIX: nodes_working,
                })



        if not nodes_working:
            self.finished_nodes = []
            #messages.success(run_settings, '%d: All processes in current iteration completed' % (self.id + 1))
        if self.output_transfer_begin:
            setvals(run_settings, {
                '%s/stages/run/finished_nodes' % django_settings.SCHEMA_PREFIX: str(self.finished_nodes),
                '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX: str(self.all_processes),
                '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX: str(self.current_processes),
                '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX: str(self.executed_procs),
                '%s/stages/wait/output_transfer_start_time' % django_settings.SCHEMA_PREFIX: self.output_transfer_start_time,
                '%s/stages/wait/output_transfer_end_time' % django_settings.SCHEMA_PREFIX: self.output_transfer_end_time,
                '%s/stages/wait/output_transfer_total_time' % django_settings.SCHEMA_PREFIX: str(self.output_transfer_total_time)[:-7],
                '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_start_time,
                #'%s/stages/wait/wait_stage_end_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_end_time,
                #'%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX: wait_stage_total_time,
                })
        else:
            setvals(run_settings, {
                '%s/stages/run/finished_nodes' % django_settings.SCHEMA_PREFIX: str(self.finished_nodes),
                '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX: str(self.all_processes),
                '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX: str(self.current_processes),
                '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX: str(self.executed_procs),
                '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_start_time,
                #'%s/stages/wait/wait_stage_end_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_end_time,
                #'%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX: wait_stage_total_time,
                })

        if self.failed_nodes:
            setval(run_settings, '%s/stages/create/failed_nodes' % django_settings.SCHEMA_PREFIX, self.failed_nodes)
            # run_settings.setdefault(

        completed_procs = [x for x in self.executed_procs if x['status'] == 'completed']
        # messages.info(run_settings, "%s: waiting (%s of %s processes done)"
        #     % (self.id + 1, len(completed_procs), len(self.current_processes) - (self.failed_processes)))


        if self.procs_2b_rescheduled:
            setvals(run_settings, {
                    '%s/stages/schedule/scheduled_started' % django_settings.SCHEMA_PREFIX: 0,
                    '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX: self.procs_2b_rescheduled
                    })
        return run_settings

def retrieve_local_settings(run_settings, local_settings):
    stage.copy_settings(local_settings, run_settings,
        '%s/stages/setup/payload_destination' % django_settings.SCHEMA_PREFIX)
    stage.copy_settings(local_settings, run_settings,
        '%s/system/platform' % django_settings.SCHEMA_PREFIX)
    stage.copy_settings(local_settings, run_settings,
        '%s/stages/setup/process_output_dirname' % django_settings.SCHEMA_PREFIX)
    stage.copy_settings(local_settings, run_settings,
        '%s/system/contextid' % django_settings.SCHEMA_PREFIX)
    stage.copy_settings(local_settings, run_settings,
    '%s/stages/setup/smart_connector_input' % django_settings.SCHEMA_PREFIX)
    local_settings['bdp_username'] = run_settings[
        django_settings.SCHEMA_PREFIX + '/bdp_userprofile']['username']

    logger.debug('retrieve completed')
