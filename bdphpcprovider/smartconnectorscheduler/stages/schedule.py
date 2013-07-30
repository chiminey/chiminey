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

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector, hrmcstages
from bdphpcprovider.smartconnectorscheduler import botocloudconnector, sshconnector
from bdphpcprovider.smartconnectorscheduler import models
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


class Schedule(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.boto_settings = user_settings.copy()
        logger.debug('Schedule stage initialised')

    def triggered(self, run_settings):
        try:
            bootstrap_done = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/bootstrap/bootstrap_done'))
            #FIXme comment group id in bootstrap.py and execute.py
            #self.group_id = smartconnector.get_existing_key(run_settings,
            #    'http://rmit.edu.au/schemas/stages/create/group_id')
            if not bootstrap_done:
                return False
        except KeyError, e:
            logger.error(e)
            return False

        bootstrapped_str = run_settings['http://rmit.edu.au/schemas/stages/bootstrap'][u'bootstrapped_nodes']
        self.bootstrapped_nodes = ast.literal_eval(bootstrapped_str)
        try:
            scheduled_str = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/scheduled_nodes')
            self.scheduled_nodes = ast.literal_eval(scheduled_str)
            logger.debug('scheduled nodes=%d, boostrapped nodes = %d'
                         % (len(self.scheduled_nodes), len(self.bootstrapped_nodes)))
            return len(self.scheduled_nodes) < len(self.bootstrapped_nodes)
        except KeyError, e:
            self.scheduled_nodes = []
            return True
        return False

    def process(self, run_settings):
        try:
            self.started = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/schedule_started'))
        except KeyError:
            self.started = 0
        retrieve_boto_settings(run_settings, self.boto_settings,
                               self.user_settings)
        self.nodes = botocloudconnector.get_rego_nodes(
                self.boto_settings, node_type='bootstrapped_nodes')

        if not self.started:
            #FIXme replace with hrmcstage.get_parent_stage()
            schedule_package = "bdphpcprovider.smartconnectorscheduler.stages.schedule.Schedule"
            parent_obj = models.Stage.objects.get(package=schedule_package)
            parent_stage = parent_obj.parent
            try:
                logger.debug('parent_package=%s' % (parent_stage.package))
                stage = hrmcstages.safe_import(parent_stage.package, [],
                                               {'user_settings': self.boto_settings})
            except ImproperlyConfigured, e:
                logger.debug(e)
                return (False, "Except in import of stage: %s: %s"
                    % (parent_stage.name, e))
            map = stage.get_run_map(self.boto_settings, run_settings=run_settings)
            try:
                isinstance(map, tuple)
                self.run_map = map[0]
            except TypeError:
                self.run_map = map
            logger.debug('map=%s' % self.run_map)
            self.total_processes = stage.get_total_templates([self.run_map])
            logger.debug('total_processes=%d' % self.total_processes)
            try:
                self.schedule_index = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/schedule_index'))
            except KeyError:
                self.schedule_index = 0

            self.schedule_index, self.current_processes = \
                start_round_robin_schedule(self.nodes, self.total_processes,
                                           self.schedule_index,
                                           self.boto_settings)
            try:
                all_processes_str = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/all_processes')
                self.all_processes = ast.literal_eval(all_processes_str)
            except KeyError:
                self.all_processes = []


            self.all_processes = update_lookup_table(
                self.current_processes, self.all_processes)
            logger.debug('all_processes=%s' % self.all_processes)
            logger.debug('schedule_index=%d' % self.schedule_index)
        else:
            for node in self.nodes:
                if not botocloudconnector.is_instance_running(node):
                    # An unlikely situation where the node crashed after is was
                    # detected as registered.
                    #FIXME: should error nodes be counted as finished?
                    #FIXME: remove this instance from created_nodes
                    logging.error('Instance %s not running' % node.id)
                    self.error_nodes.append((node.id, node.ip_address,
                                            unicode(node.region)))
                    continue
                node_ip = node.ip_address
                relative_path = "%s@%s" % (self.boto_settings['platform'],
                    self.boto_settings['payload_destination'])
                destination = smartconnector.get_url_with_pkey(self.boto_settings,
                    relative_path,
                    is_relative_path=True,
                    ip_address=node_ip)
                logger.debug("Relative path %s" % relative_path)
                logger.debug("Destination %s" % destination)
                fin = job_finished(node_ip, self.boto_settings, destination)
                logger.debug("fin=%s" % fin)
                if fin:
                    print "done."
                    logger.debug("node=%s" % str(node))
                    logger.debug("scheduled_nodes=%s" % self.bootstrapped_nodes)
                    if not (node.ip_address in [x[1] for x in self.scheduled_nodes]):
                        logger.debug('new ip = %s' % node.ip_address)
                        self.scheduled_nodes.append((node.id, node.ip_address,
                                                    unicode(node.region)))
                    else:
                        logger.info("We have already "
                            + "scheduled process on node %s" % node.ip_address)
                else:
                    print "job still running on %s" % node.ip_address

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'scheduled_nodes'] = str(self.scheduled_nodes)

        if not self.started:
            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'total_processes'] = str(self.total_processes)

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_started'] = 1

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_index'] = self.schedule_index

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'all_processes'] = str(self.all_processes)

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'current_processes'] = str(self.current_processes)

        if len(self.scheduled_nodes) == len(self.bootstrapped_nodes):
            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_completed'] = 1
        return run_settings


def retrieve_boto_settings(run_settings, boto_settings, user_settings):
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
    #smartconnector.copy_settings(boto_settings, run_settings,
    #    'http://rmit.edu.au/schemas/stages/setup/payload_source')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_destination')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/filename_for_PIDs')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_name')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/system/platform')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/bootstrap/bootstrapped_nodes')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/custom_prompt')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/nectar_username')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/nectar_password')
    boto_settings['username'] = \
        run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
    boto_settings['username'] = 'root'  # FIXME: schema value is ignored
    boto_settings['password'] = \
        run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
    key_file = hrmcstages.retrieve_private_key(
        boto_settings, user_settings['nectar_private_key'])
    boto_settings['private_key'] = key_file
    boto_settings['nectar_private_key'] = key_file


def start_round_robin_schedule(nodes, processes, schedule_index, settings):
    total_nodes = len(nodes)
    if total_nodes > processes:
        total_nodes = processes
    proc_per_node = processes / total_nodes
    remaining_procs = processes % total_nodes
    index = schedule_index
    new_processes = []
    for cur_node in nodes:
        ip_address = cur_node.ip_address
        logger.debug('ip_address=%s' % ip_address)
        relative_path = settings['platform'] + '@' + settings['payload_destination']
        procs_on_cur_node = proc_per_node
        if remaining_procs:
            procs_on_cur_node = proc_per_node + 1
            remaining_procs -= 1
        logger.debug('procs_cur_node=%d' % procs_on_cur_node)
        ids = get_procs_ids(index, procs_on_cur_node)
        index += len(ids)
        logger.debug('index=%d' % index)
        put_proc_ids(relative_path, ids, ip_address, settings)
        new_processes = construct_lookup_table(
            ids, ip_address, new_processes)

        destination = smartconnector.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=cur_node.ip_address)
        logger.debug('schedule destination=%s' % destination)
        makefile_path = hrmcstages.get_make_path(destination)
        logger.debug('makefile_path=%s' % makefile_path)
        command = "cd %s; make %s" % (makefile_path,
            'schedulestart PAYLOAD_NAME=%s IDS=%s' % (
            settings['payload_name'], settings['filename_for_PIDs']))
        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip_address)
        try:
            ssh = sshconnector.open_connection(ip_address=ip_address, settings=settings)
            command_out, errs = sshconnector.run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
    logger.debug('index=%d' % index)
    logger.debug('current_processes=%s' % new_processes)
    return index, new_processes


def get_procs_ids(index, process):
    ids = []
    for i in range(process):
        ids.append(index+1)
        index += 1
    logger.debug('process ids = %s' % ids)
    return ids


def put_proc_ids(relative_path, ids, ip, settings):
    relative_path = os.path.join(relative_path,
                                 settings['filename_for_PIDs'])
    destination = smartconnector.get_url_with_pkey(settings,
        relative_path,
        is_relative_path=True,
        ip_address=ip)
    ids_str = []
    [ids_str.append(str(i)) for i in ids]
    proc_ids = ("\n".join(ids_str)) + "\n"
    logger.debug('ids_str=%s' % ids_str)
    logger.debug('proc_ids=%s' % proc_ids)
    logger.debug('encoded=%s' % proc_ids.encode('utf-8'))
    hrmcstages.put_file(destination, proc_ids.encode('utf-8'))


def construct_lookup_table(ids, ip_address, new_processes):
    for id in ids:
        new_processes.append(
            {'status': 'ready', 'id': '%s' % id, 'ip_address': '%s' % ip_address})
    return new_processes


def update_lookup_table(new_processes, all_processes):
    for process in new_processes:
        all_processes.append(process)
    return all_processes


#FIXME: what happens if a job never finishes?
def job_finished(ip, settings, destination):
    """
        Return True if package job on instance_id has job_finished
    """
    ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
    makefile_path = hrmcstages.get_make_path(destination)
    command = "cd %s; make %s" % (makefile_path,
                                  'scheduledone IDS=%s' % (
                                      settings['filename_for_PIDs']))
    command_out, _ = sshconnector.run_command_with_status(ssh, command)
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'All processes are scheduled' in line:
                return True
    return False


