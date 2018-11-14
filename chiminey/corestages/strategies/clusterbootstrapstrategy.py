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

import ast
import logging
from chiminey.reliabilityframework import FTManager
from chiminey import messages
from chiminey.runsettings import getval, update
from chiminey.corestages.errors \
    import InsufficientResourceError, VMTerminatedError
from chiminey.storage import get_url_with_credentials, copy_directories, get_make_path
from chiminey.sshconnection import open_connection
from chiminey.compute import run_command_with_status, run_make
from chiminey.cloudconnection import NoRegisteredVMError
from django.conf import settings as django_settings


logger = logging.getLogger(__name__)
RMIT_SCHEMA = django_settings.SCHEMA_PREFIX


def set_bootstrap_settings(run_settings, local_settings):
    #logger.debug('in=%s' % run_settings)
    update(local_settings, run_settings,
           '%s/stages/setup/payload_source' % RMIT_SCHEMA,
           '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
           '%s/stages/create/created_nodes' % RMIT_SCHEMA,
           '%s/system/contextid' % RMIT_SCHEMA
           )
    local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
    logger.debug('out=%s' % local_settings)


def start_multi_bootstrap_task(settings, relative_path_suffix):
    """
    Run the package on each of the nodes in the group and grab
    any output as needed
    """
    #nodes = get_registered_vms(settings)

    nodes = ast.literal_eval(settings['created_nodes'])
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
            node_ip = instance[1]

            logger.debug("node_ip=%s" % node_ip)
            logger.debug('constructing source')
            source = get_url_with_credentials(settings, "/" + settings['payload_source'])
            logger.debug('source=%s' % source)
            #relative_path = '%s@%s' % (settings['type'], settings['payload_destination'])
            relative_path = '%s@%s' % (settings['type'], relative_path_suffix)
            destination = get_url_with_credentials(settings, relative_path,
                                                 is_relative_path=True,
                                                 ip_address=node_ip)
            logger.debug("Source %s" % source)
            logger.debug("Destination %s" % destination)
            logger.debug("Relative path %s" % relative_path)
            _start_bootstrap(instance, node_ip, settings, source, destination)
            nodes.pop(0)


def _start_bootstrap(instance, ip,  settings, source, destination):
    """
        Start the task on the instance, then return
    """
    logger.info("run_task %s" % str(instance))
    copy_directories(source, destination, job_id=str(settings['contextid']), message='BootstrapStage')
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
        run_make(ssh, makefile_path, 'start_bootstrap')
    except Exception, e:#fixme: consider using reliability framework
        logger.error(e)
        raise
    finally:
        if ssh:
            ssh.close()


def complete_bootstrap(bootstrap_class, local_settings):
    try:

        nodes = ast.literal_eval(local_settings['created_nodes'])
        logger.debug("nodes=%s" % nodes)

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
        node_ip = node[1]
        if (node_ip in [x[1] for x in bootstrap_class.bootstrapped_nodes if x[1] == node_ip]):
            continue
        relative_path_suffix = bootstrap_class.get_relative_output_path(local_settings)
        relative_path = "%s@%s" % (local_settings['type'],
            relative_path_suffix)
        destination = get_url_with_credentials(local_settings,
            relative_path,
            is_relative_path=True,
            ip_address=node_ip)
        logger.debug("Relative path %s" % relative_path)
        logger.debug("Destination %s" % destination)
        try:
            fin = _is_bootstrap_complete(node_ip, local_settings, destination)
        except IOError, e:
            logger.error(e)
            fin = False
        except Exception as e:
            logger.error(e)
            fin = False
            ftmanager = FTManager()
            ftmanager.manage_failure(e, stage_class=bootstrap_class, vm_ip=node_ip,
                                     vm_id=node[0], settings=local_settings)
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
                    [node[0], node_ip, node[2], 'running'])
            else:
                logger.info("We have already "
                    + "bootstrapped node %s" % node_ip)
            messages.info_context(local_settings['contextid'],
                                  "bootstrapping nodes (%s nodes done)"
                % len(bootstrap_class.bootstrapped_nodes))
        else:
            print "job still running on %s" % node_ip


def _is_bootstrap_complete(ip, settings, destination):
    """
        Return True if package job on instance_id has is_job_finished
    """
    ssh = open_connection(ip_address=ip, settings=settings)
    makefile_path = get_make_path(destination)
    (command_out, err) = run_make(ssh, makefile_path, 'bootstrap_done')
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'Environment Setup Completed' in line:
                return True
    else:
        logger.warn(err)
    return False
