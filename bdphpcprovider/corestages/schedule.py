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
import ast
import os
from pprint import pformat

from django.core.exceptions import ImproperlyConfigured

from bdphpcprovider.cloudconnection import get_registered_vms, is_vm_running
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages import stage
from bdphpcprovider.corestages.stage import Stage
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status

from bdphpcprovider import storage

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Schedule(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        logger.debug('Schedule stage initialised')

    def triggered(self, run_settings):
        #fixme what happens if no nodes are available for scheduling
        try:
            failed_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'failed_nodes']
            failed_nodes = ast.literal_eval(failed_str)
            created_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'created_nodes']
            created_nodes = ast.literal_eval(created_str)
            if len(failed_nodes) == len(created_nodes) or len(created_nodes) == 0:
                return False
        except KeyError, e:
            logger.debug(e)

        try:
            bootstrap_done = int(stage.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/bootstrap/bootstrap_done'))
            if not bootstrap_done:
                return False
        except KeyError, e:
            return False
        bootstrapped_str = run_settings['http://rmit.edu.au/schemas/stages/bootstrap'][u'bootstrapped_nodes']
        self.bootstrapped_nodes = ast.literal_eval(bootstrapped_str)
        if len(self.bootstrapped_nodes) == 0:
            return False

        try:
            reschedule_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'procs_2b_rescheduled']
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
        except KeyError, e:
            logger.debug(e)
            self.procs_2b_rescheduled = []

        if self.procs_2b_rescheduled:
            #self.trigger_reschedule(run_settings)
            try:
                self.total_rescheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_rescheduled_procs']
            except KeyError:
                self.total_rescheduled_procs = 0
            self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
            if (self.total_procs_2b_rescheduled == self.total_rescheduled_procs) and self.total_rescheduled_procs:
                return False
        else:
            try:
                self.total_scheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_scheduled_procs']
            except KeyError:
                self.total_scheduled_procs = 0

            try:
                total_procs = int(run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_processes'])
                if total_procs:
                    if total_procs == self.total_scheduled_procs:
                        return False
            except KeyError, e:
                logger.debug(e)

        try:
            scheduled_str = stage.get_existing_key(
                run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/scheduled_nodes')
            self.scheduled_nodes = ast.literal_eval(scheduled_str)
            #current_processes_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
            #self.current_processes = ast.literal_eval(current_processes_str)
        except KeyError, e:
            self.scheduled_nodes = []

        try:
            rescheduled_str = stage.get_existing_key(
                run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/rescheduled_nodes')
            self.rescheduled_nodes = ast.literal_eval(rescheduled_str)
        except KeyError, e:
            self.rescheduled_nodes = []

        try:
            current_processes_str = stage.get_existing_key(
                run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/current_processes')
            #self.scheduled_nodes = ast.literal_eval(scheduled_str)
            #current_processes_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
            self.current_processes = ast.literal_eval(current_processes_str)
        except KeyError, e:
            self.current_processes = []

        try:
            all_processes_str = stage.get_existing_key(run_settings,
            'http://rmit.edu.au/schemas/stages/schedule/all_processes')
            self.all_processes = ast.literal_eval(all_processes_str)
        except KeyError:
            self.all_processes = []

        return True

    def trigger_schedule(self, run_settings):
        try:
            self.total_scheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_scheduled_procs']
        except KeyError:
            self.total_scheduled_procs = 0

        try:
            total_procs = int(run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_processes'])
            if total_procs:
                if total_procs == self.total_scheduled_procs:
                    return False
        except KeyError, e:
            logger.debug(e)

    def trigger_reschedule(self, run_settings):

        try:
            self.total_rescheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_rescheduled_procs']
        except KeyError:
            self.total_rescheduled_procs = 0
        self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
        if self.total_procs_2b_rescheduled == self.total_rescheduled_procs:
            return False

    def process(self, run_settings):
        try:
            self.started = int(stage.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/schedule_started'))
        except KeyError:
            self.started = 0
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        retrieve_local_settings(run_settings, local_settings)
        logger.debug('Schedule here')
        self.nodes = get_registered_vms(
                local_settings, node_type='bootstrapped_nodes')
        logger.debug('Schedule there')
        if not self.started:
            try:
                self.schedule_index = int(stage.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/schedule_index'))
            except KeyError:
                self.schedule_index = 0

            if self.procs_2b_rescheduled:
                self.start_reschedule(run_settings, local_settings)
            else:
                self.start_schedule(run_settings, local_settings)

            #self.current_processes = []
            logger.debug('schedule_index=%d' % self.schedule_index)

        else:
            for node in self.nodes:
                node_ip = node.ip_address
                if not node_ip:
                    node_ip = node.private_ip_address
                if (node_ip in [x[1]
                                        for x in self.scheduled_nodes
                                        if x[1] == node_ip]) \
                    and (not self.procs_2b_rescheduled):
                    continue
                if (node_ip in [x[1]
                                        for x in self.rescheduled_nodes
                                        if x[1] == node_ip]) \
                    and self.procs_2b_rescheduled:
                    continue
                if not is_vm_running(node):
                    # An unlikely situation where the node crashed after is was
                    # detected as registered.
                    #FIXME: should error nodes be counted as finished?
                    #FIXME: remove this instance from created_nodes
                    logging.error('Instance %s not running' % node.id)
                    self.error_nodes.append((node.id, node_ip,
                                            unicode(node.region)))
                    continue

                logger.debug('mynode=%s' % node_ip)
                try:
                    relative_path = "%s@%s" % (local_settings['type'],
                        local_settings['payload_destination'])
                    destination = stage.get_url_with_pkey(
                        local_settings,
                        relative_path,
                        is_relative_path=True,
                        ip_address=node_ip)
                except Exception, e:
                    logger.debug(e)
                logger.debug("Relative path %s" % relative_path)
                logger.debug("Destination %s" % destination)
                fin = job_finished(node_ip, local_settings, destination)
                logger.debug("fin=%s" % fin)
                if fin:
                    logger.debug("done.")
                    node_list = self.scheduled_nodes
                    if self.procs_2b_rescheduled:
                        node_list = self.rescheduled_nodes
                    if not (node_ip in [x[1]
                                                    for x in node_list
                                                    if x[1] == node_ip]):
                            node_list.append((node.id, node_ip,
                                                        unicode(node.region)))
                            if self.procs_2b_rescheduled:
                                scheduled_procs = [x
                                                   for x in self.current_processes
                                                   if x['ip_address'] == node_ip
                                    and x['status'] == 'reschedule_ready']
                                self.total_rescheduled_procs += len(scheduled_procs)
                                for process in scheduled_procs:
                                    process['status'] = 'ready'
                                self.all_processes = update_lookup_table(
                                    self.all_processes,
                                    reschedule_to_ready='reschedule_to_ready')
                            else:
                                scheduled_procs = [x['ip_address']
                                                   for x in self.current_processes
                                                   if x['ip_address'] == node_ip]
                                self.total_scheduled_procs += len(scheduled_procs)
                                #if self.total_scheduled_procs == len(self.current_processes):
                                #    break
                    else:
                            logger.info("We have already "
                                + "scheduled process on node %s" % node_ip)
                else:
                    print "job still running on %s" % node_ip
        #logger.debug('exit total_scheduled_procs=%d' % self.total_scheduled_procs)

    def start_schedule(self, run_settings, local_settings):
        #FIXme replace with hrmcstage.get_parent_stage()
        schedule_package = "bdphpcprovider.corestages.schedule.Schedule"
        parent_obj = models.Stage.objects.get(package=schedule_package)
        parent_stage = parent_obj.parent
        logger.debug("local_settings=%s" % local_settings)
        logger.debug("run_settings=%s" % run_settings)
        try:
            logger.debug('parent_package=%s' % (parent_stage.package))
            stage = hrmcstages.safe_import(parent_stage.package, [],
                                           {'user_settings': local_settings})
            logger.debug("stage=%s" % stage)
        except ImproperlyConfigured, e:
            logger.debug(e)
            return (False, "Except in import of stage: %s: %s"
                % (parent_stage.name, e))
        except Exception, e:
            logger.error(e)
            raise

        map = stage.get_run_map(local_settings, run_settings=run_settings)
        try:
            isinstance(map, tuple)
            self.run_map = map[0]
        except TypeError:
            self.run_map = map
        logger.debug('map=%s' % self.run_map)

        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        job_dir = manage.get_job_dir(output_storage_settings, offset)
        self.total_processes = stage.get_total_templates(
            [self.run_map], run_settings=run_settings,
            output_storage_settings=output_storage_settings, job_dir=job_dir)
        logger.debug('total_processes=%d' % self.total_processes)

        self.current_processes = []
        self.schedule_index, self.current_processes = \
                start_round_robin_schedule(self.nodes, self.total_processes,
                                           self.schedule_index,
                                           local_settings)
        self.all_processes = update_lookup_table(
                 self.all_processes, new_processes=self.current_processes)
        logger.debug('all_processes=%s' % self.all_processes)

    def start_reschedule(self, run_settings, local_settings):
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        _, self.current_processes = \
        start_round_robin_reschedule(self.nodes, self.procs_2b_rescheduled,
                                     self.current_processes, local_settings, output_storage_settings)
        self.all_processes = update_lookup_table(
                 self.all_processes,
                 new_processes=self.current_processes, reschedule=True)

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'scheduled_nodes'] = str(self.scheduled_nodes)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'rescheduled_nodes'] = str(self.rescheduled_nodes)
        run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'all_processes'] = str(self.all_processes)
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'current_processes'] = str(self.current_processes)
        if not self.started:
            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_started'] = 1
            run_settings.setdefault(
                    'http://rmit.edu.au/schemas/stages/schedule',
                    {})[u'procs_2b_rescheduled'] = self.procs_2b_rescheduled
            if not self.procs_2b_rescheduled:
                run_settings.setdefault(
                    'http://rmit.edu.au/schemas/stages/schedule',
                    {})[u'total_processes'] = str(self.total_processes)
                run_settings.setdefault(
                    'http://rmit.edu.au/schemas/stages/schedule',
                    {})[u'schedule_index'] = self.schedule_index
        else:
            if self.procs_2b_rescheduled:
                run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'total_rescheduled_procs'] = self.total_rescheduled_procs
                if self.total_rescheduled_procs == len(self.procs_2b_rescheduled):
                    run_settings.setdefault(
                        'http://rmit.edu.au/schemas/stages/schedule',
                        {})[u'schedule_completed'] = 1
                    run_settings.setdefault(
                        'http://rmit.edu.au/schemas/stages/schedule',
                        {})[u'procs_2b_rescheduled'] = []
                    run_settings.setdefault(
                        'http://rmit.edu.au/schemas/stages/schedule',
                        {})[u'total_rescheduled_procs'] = 0
                    run_settings.setdefault(
                        'http://rmit.edu.au/schemas/stages/schedule',
                        {})[u'rescheduled_nodes'] = []
            else:
                run_settings.setdefault(
                    'http://rmit.edu.au/schemas/stages/schedule',
                    {})[u'total_scheduled_procs'] = self.total_scheduled_procs
                if self.total_scheduled_procs == len(self.current_processes):
                    run_settings.setdefault(
                        'http://rmit.edu.au/schemas/stages/schedule',
                        {})[u'schedule_completed'] = 1

        return run_settings


def retrieve_local_settings(run_settings, local_settings):
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/system/cloud/number_vm_instances')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/reliability/maximum_retry')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_destination')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/filename_for_PIDs')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_name')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/platform')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/bootstrap/bootstrapped_nodes')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/custom_prompt')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/max_seed_int')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
    stage.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result')
    local_settings['bdp_username'] = run_settings[
        RMIT_SCHEMA + '/bdp_userprofile']['username']

    computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
    comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
    local_settings.update(comp_pltf_settings)

    logger.debug('retrieve completed %s' % pformat(local_settings))


def start_round_robin_schedule(nodes, processes, schedule_index, settings):
    total_nodes = len(nodes)
    all_nodes = list(nodes)
    if total_nodes > processes:
        total_nodes = processes
        all_nodes = nodes[:total_nodes]
    if total_nodes == 0:
        return
    proc_per_node = processes / total_nodes
    remaining_procs = processes % total_nodes
    index = schedule_index
    new_processes = []

    for cur_node in all_nodes:
        ip_address = cur_node.ip_address
        if not ip_address:
            ip_address = cur_node.private_ip_address
        logger.debug('ip_address=%s' % ip_address)
        relative_path = settings['type'] + '@' + settings['payload_destination']
        procs_on_cur_node = proc_per_node
        if remaining_procs:
            procs_on_cur_node = proc_per_node + 1
            remaining_procs -= 1
        logger.debug('procs_cur_node=%d' % procs_on_cur_node)
        ids = get_procs_ids(procs_on_cur_node, index=index)
        index += len(ids)
        logger.debug('index=%d' % index)
        put_proc_ids(relative_path, ids, ip_address, settings)
        new_processes = construct_lookup_table(
            ids, ip_address, new_processes,
            maximum_retry=int(settings['maximum_retry']))

        destination = stage.get_url_with_pkey(
            settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip_address)
        logger.debug('schedule destination=%s' % destination)
        makefile_path = storage.get_make_path(destination)
        logger.debug('makefile_path=%s' % makefile_path)
        command = "cd %s; make %s" % (makefile_path,
            'schedulestart PAYLOAD_NAME=%s IDS=%s' % (
            settings['payload_name'], settings['filename_for_PIDs']))
        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip_address)
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            command_out, errs = run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
    logger.debug('index=%d' % index)
    logger.debug('current_processes=%s' % new_processes)
    return index, new_processes


def start_round_robin_reschedule(nodes, procs_2b_rescheduled,
                                 current_procs, settings, output_storage_settings):
    total_nodes = len(nodes)
    all_nodes = list(nodes)
    processes = len(procs_2b_rescheduled)
    if total_nodes > processes:
        total_nodes = processes
        all_nodes = nodes[:total_nodes]
    if total_nodes == 0:
        return
    proc_per_node = processes / total_nodes
    remaining_procs = processes % total_nodes
    index = 0
    new_processes = current_procs
    rescheduled_procs = list(procs_2b_rescheduled)
    for cur_node in all_nodes:
        logger.debug('Schedule here %s' % cur_node)
        ip_address = cur_node.ip_address
        if not ip_address:
            ip_address = cur_node.private_ip_address
        logger.debug('ip_address=%s' % ip_address)
        relative_path = output_storage_settings['type'] + '@' + settings['payload_destination']
        procs_on_cur_node = proc_per_node
        if remaining_procs:
            procs_on_cur_node = proc_per_node + 1
            remaining_procs -= 1
        logger.debug('procs_cur_node=%d' % procs_on_cur_node)
        ids = get_procs_ids(procs_on_cur_node,
                            rescheduled_procs=rescheduled_procs)
        #index += len(ids)
        #logger.debug('index=%d' % index)
        put_proc_ids(relative_path, ids, ip_address, settings)
        new_processes = construct_lookup_table(
            ids, ip_address, new_processes,
            status='reschedule_ready',
            maximum_retry=int(settings['maximum_retry']))
        destination = stage.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip_address)
        logger.debug('schedule destination=%s' % destination)
        makefile_path = storage.get_make_path(destination)
        logger.debug('makefile_path=%s' % makefile_path)
        command = "cd %s; make %s" % (makefile_path,
            'schedulestart PAYLOAD_NAME=%s IDS=%s' % (
            settings['payload_name'], settings['filename_for_PIDs']))
        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip_address)
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            command_out, errs = run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
    logger.debug('index=%d' % index)
    logger.debug('current_processes=%s' % new_processes)
    return index, new_processes


def get_procs_ids(process, **kwargs):
    ids = []
    try:
        index = kwargs['index']
        for i in range(process):
            ids.append(index + 1)
            index += 1
    except KeyError, e:
        logger.debug(e)
    try:
        rescheduled_procs = kwargs['rescheduled_procs']
        for i in range(process):
            reschedule_process = rescheduled_procs[0]
            ids.append(reschedule_process['id'])
            rescheduled_procs.pop(0)
    except KeyError, e:
        logger.debug(e)
    logger.debug('process ids = %s' % ids)
    return ids


def put_proc_ids(relative_path, ids, ip, settings):
    relative_path = os.path.join(relative_path,
                                 settings['filename_for_PIDs'])
    logger.debug('put_proc_ids=%s' % relative_path)
    destination = stage.get_url_with_pkey(settings,
        relative_path,
        is_relative_path=True,
        ip_address=ip)
    logger.debug('destination=%s' % destination)
    ids_str = []
    [ids_str.append(str(i)) for i in ids]
    proc_ids = ("\n".join(ids_str)) + "\n"
    logger.debug('ids_str=%s' % ids_str)
    logger.debug('proc_ids=%s' % proc_ids)
    logger.debug('encoded=%s' % proc_ids.encode('utf-8'))
    storage.put_file(destination, proc_ids.encode('utf-8'))


def construct_lookup_table(ids, ip_address, new_processes, maximum_retry=1, status='ready'):
    for id in ids:
        new_processes.append(
            {'status': '%s' % status, 'id': '%s' % id,
             'ip_address': '%s' % ip_address,
             'retry_left': '%d' % maximum_retry})
    return new_processes


def update_lookup_table(all_processes, reschedule=False, **kwargs):
    try:
        new_processes = kwargs['new_processes']
        if not reschedule:
            for process in new_processes:
                all_processes.append(process)
        else:
            for process in new_processes:
                if process['status'] == 'reschedule_ready':
                    all_processes.append(process)
    except KeyError, e:
        logger.debug(e)
    try:
        reschedule_to_ready = kwargs['reschedule_to_ready']
        for process in all_processes:
            if process['status'] == 'reschedule_ready':
                process['status'] = 'ready'
    except KeyError, e:
        logger.debug(e)
    return all_processes


#FIXME: what happens if a job never finishes?
def job_finished(ip, settings, destination):
    """
        Return True if package job on instance_id has job_finished
    """
    ssh = open_connection(ip_address=ip, settings=settings)
    makefile_path = storage.get_make_path(destination)
    command = "cd %s; make %s" % (makefile_path,
                                  'scheduledone IDS=%s' % (
                                      settings['filename_for_PIDs']))
    command_out, _ = run_command_with_status(ssh, command)
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'All processes are scheduled' in line:
                return True
    return False
