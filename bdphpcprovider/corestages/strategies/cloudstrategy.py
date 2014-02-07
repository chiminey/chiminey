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
from bdphpcprovider.cloudconnection import create_vms, destroy_vms, print_vms
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientVMError
from bdphpcprovider.reliabilityframework import FTManager
from bdphpcprovider import messages
from bdphpcprovider.runsettings import SettingNotFoundException, getval, update
from bdphpcprovider.cloudconnection import get_registered_vms
from bdphpcprovider.smartconnectorscheduler.stages.errors \
    import InsufficientResourceError, VMTerminatedError, NoRegisteredVMError
from bdphpcprovider.storage import get_url_with_pkey, copy_directories, get_make_path
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status, run_make
from bdphpcprovider.corestages.strategies import schedulestrategy as schedule

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
        update(local_settings, run_settings,
               '%s/stages/setup/payload_source' % RMIT_SCHEMA,
               '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
               '%s/stages/create/created_nodes' % RMIT_SCHEMA,
               '%s/system/contextid' % RMIT_SCHEMA
               )
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

    def start_multi_bootstrap_task(self, settings):
        """
        Run the package on each of the nodes in the group and grab
        any output as needed
        """
        nodes = get_registered_vms(settings)
        logger.debug("nodes=%s" % nodes)
        requested_nodes = 0
        maketarget_nodegroup_pair = {}

        # TODO: need testcases for following code
        if not maketarget_nodegroup_pair:
            EMPTY_MAKE_TARGET = ''
            requested_nodes = len(nodes)
            maketarget_nodegroup_pair[EMPTY_MAKE_TARGET] = requested_nodes
        else:
            for i in maketarget_nodegroup_pair.keys():
                requested_nodes += maketarget_nodegroup_pair[i]
            if requested_nodes > len(nodes):
                message = "Requested nodes %d; but available nodes %s " \
                    % (requested_nodes, len(nodes))
                logger.exception(message)
                raise InsufficientResourceError(message)
        logger.info("Requested nodes %d: \nAvailable nodes %s "
               % (requested_nodes, len(nodes)))

        logger.debug('starting setup')
        for make_target in maketarget_nodegroup_pair:
            for i in range(0, maketarget_nodegroup_pair[make_target]):
                instance = nodes[0]
                node_ip = instance.ip_address
                if not node_ip:
                    node_ip = instance.private_ip_address
                logger.debug("node_ip=%s" % node_ip)
                logger.debug('constructing source')
                source = get_url_with_pkey(settings, settings['payload_source'])
                logger.debug('source=%s' % source)
                relative_path = '%s@%s' % (settings['type'], settings['payload_destination'])
                destination = get_url_with_pkey(settings, relative_path,
                                                     is_relative_path=True,
                                                     ip_address=node_ip)
                logger.debug("Source %s" % source)
                logger.debug("Destination %s" % destination)
                logger.debug("Relative path %s" % relative_path)
                self._start_bootstrap(instance, node_ip, settings, source, destination)
                nodes.pop(0)

    def _start_bootstrap(self, instance, ip,  settings, source, destination):
        """
            Start the task on the instance, then return
        """
        logger.info("run_task %s" % str(instance))
        copy_directories(source, destination)
        makefile_path = get_make_path(destination)
        # TODO, FIXME:  need to have timeout for yum install make
        # and then test can access, otherwise, loop.
        install_make = 'yum install -y make'
        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip)
        ssh = ''
        try:
            ssh = open_connection(ip_address=ip, settings=settings)
            command_out, errs = run_command_with_status(ssh, install_make)
            logger.debug("command_out1=(%s, %s)" % (command_out, errs))
            run_make(ssh, makefile_path, 'setupstart')
        except Exception, e:#fixme: consider using reliability framework
            logger.error(e)
            raise
        finally:
            if ssh:
                ssh.close()


    def complete_bootstrap(self, bootstrap_class, local_settings):
        try:
            nodes = get_registered_vms(local_settings)
            running_created_nodes = [x for x in bootstrap_class.created_nodes if str(x[3]) == 'running']
            if len(nodes) < len(running_created_nodes):
                raise VMTerminatedError
        except NoRegisteredVMError as e:
            logger.debug('NoRegisteredVMError detected')
            ftmanager = FTManager()
            ftmanager.manage_failure(e, stage_class=bootstrap_class,  settings=local_settings)
        except VMTerminatedError as e:
            logger.debug('VMTerminatedError detected')
            ftmanager = FTManager()
            ftmanager.manage_failure(e, stage_class=bootstrap_class,  settings=local_settings)
        for node in nodes:
            node_ip = node.ip_address
            if not node_ip:
                node_ip = node.private_ip_address
            if (node_ip in [x[1] for x in bootstrap_class.bootstrapped_nodes if x[1] == node_ip]):
                continue
            relative_path = "%s@%s" % (local_settings['type'],
                local_settings['payload_destination'])
            destination = get_url_with_pkey(local_settings,
                relative_path,
                is_relative_path=True,
                ip_address=node_ip)
            logger.debug("Relative path %s" % relative_path)
            logger.debug("Destination %s" % destination)
            try:
                fin = self._is_bootstrap_complete(node_ip, local_settings, destination)
            except IOError, e:
                logger.error(e)
                fin = False
            except Exception as e:
                logger.error(e)
                fin = False
                ftmanager = FTManager()
                ftmanager.manage_failure(e, stage_class=bootstrap_class, vm_ip=node_ip,
                                         vm_id=node.id, settings=local_settings)
            logger.debug("fin=%s" % fin)
            if fin:
                print "done."
                logger.debug("node=%s" % str(node))
                logger.debug("bootstrapped_nodes=%s" % bootstrap_class.bootstrapped_nodes)
                if not (node_ip in [x[1]
                                            for x in bootstrap_class.bootstrapped_nodes
                                            if x[1] == node_ip]):
                    logger.debug('new ip = %s' % node_ip)
                    bootstrap_class.bootstrapped_nodes.append(
                        [node.id, node_ip, unicode(node.region), 'running'])
                else:
                    logger.info("We have already "
                        + "bootstrapped node %s" % node_ip)
                messages.info_context(local_settings['contextid'],
                                      "bootstrapping nodes (%s nodes done)"
                    % len(bootstrap_class.bootstrapped_nodes))
            else:
                print "job still running on %s" % node_ip


    def _is_bootstrap_complete(self, ip, settings, destination):
        """
            Return True if package job on instance_id has is_job_finished
        """
        ssh = open_connection(ip_address=ip, settings=settings)
        makefile_path = get_make_path(destination)
        (command_out, err) = run_make(ssh, makefile_path, 'setupdone')
        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if 'Environment Setup Completed' in line:
                    return True
        else:
            logger.warn(err)
        return False

    def set_schedule_settings(self, run_settings, local_settings):
        #fixme: the last three should move to hrmc package
        update(local_settings, run_settings,
                #'%s/input/system/cloud/number_vm_instances' % RMIT_SCHEMA,
                '%s/input/reliability/maximum_retry' % RMIT_SCHEMA,
                '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
                '%s/stages/setup/filename_for_PIDs' % RMIT_SCHEMA,
                '%s/stages/setup/payload_name' % RMIT_SCHEMA,
                #'%s/system/platform' % RMIT_SCHEMA,
                '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA,
                #'%s/stages/create/custom_prompt' % RMIT_SCHEMA,
                '%s/system/max_seed_int' % RMIT_SCHEMA,
                '%s/input/hrmc/optimisation_scheme' % RMIT_SCHEMA,
                '%s/input/hrmc/fanout_per_kept_result' % RMIT_SCHEMA)
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

    def start_schedule_task(self, schedule_class, run_settings, local_settings):
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














