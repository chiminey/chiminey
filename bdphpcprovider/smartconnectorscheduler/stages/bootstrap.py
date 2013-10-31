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

from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import hrmcstages, platform
from bdphpcprovider.smartconnectorscheduler import sshconnector, botocloudconnector, models
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientResourceError

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

class Bootstrap(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        logger.debug('Bootstrap stage initialised')

    def triggered(self, run_settings):
        if not self._exists(run_settings, RMIT_SCHEMA+'/stages/create', u'created_nodes'):
            return False
        created_str = run_settings[RMIT_SCHEMA+'/stages/create'][u'created_nodes']
        self.created_nodes = ast.literal_eval(created_str)
        if len(self.created_nodes) == 0:
            return False
        try:
            bootstrapped_str = smartconnector.get_existing_key(run_settings,
                RMIT_SCHEMA+'/stages/bootstrap/bootstrapped_nodes')
            self.bootstrapped_nodes = ast.literal_eval(bootstrapped_str)
            logger.debug('bootstrapped nodes=%d, created nodes = %d'
                         % (len(self.bootstrapped_nodes), len(self.created_nodes)))
            return len(self.bootstrapped_nodes) < len(self.created_nodes)
        except KeyError:
            self.bootstrapped_nodes = []
            return True
        return False

    def process(self, run_settings):
        try:
            self.started = int(smartconnector.get_existing_key(run_settings,
                RMIT_SCHEMA+'/stages/bootstrap/started'))
        except KeyError:
            self.started = 0
        logger.debug('self.started=%d' % self.started)
        smartconnector.info(run_settings, "bootstrapping nodes")
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        retrieve_local_settings(run_settings, local_settings)

        if not self.started:
            try:
                logger.debug('process to start')
                _ = start_multi_setup_task(local_settings)
            except PackageFailedError, e:
                logger.error("unable to start setup of packages: %s" % e)
            except Exception, e:
                logger.debug(e)
                raise
            pass
            self.started = 1

        else:
            self.nodes = botocloudconnector.get_rego_nodes(local_settings)
            self.error_nodes = []
            for node in self.nodes:
                if (node.ip_address in [x[1]
                                        for x in self.bootstrapped_nodes
                                        if x[1] == node.ip_address]):
                    continue
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
                relative_path = "%s@%s" % (local_settings['type'],
                    local_settings['payload_destination'])
                destination = smartconnector.get_url_with_pkey(local_settings,
                    relative_path,
                    is_relative_path=True,
                    ip_address=node_ip)
                logger.debug("Relative path %s" % relative_path)
                logger.debug("Destination %s" % destination)
                try:
                    fin = job_finished(node_ip, local_settings, destination)
                except IOError, e:
                    logger.error(e)
                    fin = False
                logger.debug("fin=%s" % fin)
                if fin:
                    print "done."
                    logger.debug("node=%s" % str(node))
                    logger.debug("bootstrapped_nodes=%s" % self.bootstrapped_nodes)
                    if not (node.ip_address in [x[1]
                                                for x in self.bootstrapped_nodes
                                                if x[1] == node.ip_address]):
                        logger.debug('new ip = %s' % node.ip_address)
                        self.bootstrapped_nodes.append((node.id, node.ip_address,
                                            unicode(node.region)))
                    else:
                        logger.info("We have already "
                            + "bootstrapped node %s" % node.ip_address)
                    smartconnector.info(run_settings, "bootstrapping nodes (%s nodes done)"
                        % len(self.bootstrapped_nodes))
                else:
                    print "job still running on %s" % node.ip_address


    def output(self, run_settings):
        run_settings.setdefault(
            RMIT_SCHEMA+'/stages/bootstrap',
            {})[u'started'] = self.started
        run_settings.setdefault(
            RMIT_SCHEMA+'/stages/bootstrap',
            {})[u'bootstrapped_nodes'] = str(self.bootstrapped_nodes)
        run_settings.setdefault(
            RMIT_SCHEMA+'/system',
            {})[u'id'] = 0
        logger.debug('created_nodes=%s' % self.created_nodes)
        if len(self.bootstrapped_nodes) == len(self.created_nodes):
            run_settings.setdefault(RMIT_SCHEMA+'/stages/bootstrap',
            {})[u'bootstrap_done'] = 1

        return run_settings


def retrieve_local_settings(run_settings, local_settings):
    smartconnector.copy_settings(local_settings, run_settings,
        RMIT_SCHEMA+'/stages/setup/payload_source')
    smartconnector.copy_settings(local_settings, run_settings,
        RMIT_SCHEMA+'/stages/setup/payload_destination')
    smartconnector.copy_settings(local_settings, run_settings,
        RMIT_SCHEMA+'/system/platform')
    smartconnector.copy_settings(local_settings, run_settings,
        RMIT_SCHEMA+'/stages/create/created_nodes')
    smartconnector.copy_settings(local_settings, run_settings,
        RMIT_SCHEMA+'/stages/create/custom_prompt')

    comp_pltf_schema = run_settings['http://rmit.edu.au/schemas/platform/computation']['namespace']
    comp_pltf_settings = run_settings[comp_pltf_schema]
    platform.update_platform_settings(
        comp_pltf_schema, comp_pltf_settings)
    local_settings.update(comp_pltf_settings)

    logger.debug('retrieve completed')


def start_multi_setup_task(settings, maketarget_nodegroup_pair={}):
    """
    Run the package on each of the nodes in the group and grab
    any output as needed
    """
    nodes = botocloudconnector.get_rego_nodes(settings)
    logger.debug("nodes=%s" % nodes)
    requested_nodes = 0

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

    logger.debug('starting')
    for make_target in maketarget_nodegroup_pair:
        for i in range(0, maketarget_nodegroup_pair[make_target]):
            instance = nodes[0]
            node_ip = instance.ip_address
            logger.debug("node_ip=%s" % node_ip)
            logger.debug('constructing source')
            source = smartconnector.get_url_with_pkey(settings, settings['payload_source'])
            logger.debug('source=%s' % source)
            relative_path = '%s@%s' % (settings['type'], settings['payload_destination'])
            destination = smartconnector.get_url_with_pkey(settings, relative_path,
                                                 is_relative_path=True,
                                                 ip_address=node_ip)
            logger.debug("Source %s" % source)
            logger.debug("Destination %s" % destination)
            logger.debug("Relative path %s" % relative_path)
            start_setup(instance, node_ip, settings, source, destination)
            nodes.pop(0)


def start_setup(instance, ip,  settings, source, destination):
    """
        Start the task on the instance, then return
    """
    logger.info("run_task %s" % str(instance))
    hrmcstages.copy_directories(source, destination)
    makefile_path = hrmcstages.get_make_path(destination)

    # TODO, FIXME:  need to have timeout for yum install make
    # and then test can access, otherwise, loop.
    install_make = 'yum install -y make'
    command_out = ''
    errs = ''
    logger.debug("starting command for %s" % ip)
    ssh = ''
    try:
        ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
        command_out, errs = sshconnector.run_command_with_status(ssh, install_make)
    except Exception, e:
        logger.error(e)
    finally:
        if ssh:
            ssh.close()
    logger.debug("command_out1=(%s, %s)" % (command_out, errs))

    command = "cd %s; make %s" % (makefile_path, 'setupstart')
    command_out = ''
    errs = ''
    logger.debug("starting command for %s" % ip)
    try:
        ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
        command_out, errs = sshconnector.run_command_with_status(ssh, command)
    except Exception, e:
        logger.error(e)
    finally:
        if ssh:
            ssh.close()
    logger.debug("command_out2=(%s, %s)" % (command_out, errs))


def job_finished(ip, settings, destination):
    """
        Return True if package job on instance_id has job_finished
    """
    ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
    makefile_path = hrmcstages.get_make_path(destination)
    command = "cd %s; make %s" % (makefile_path, 'setupdone')
    command_out, _ = sshconnector.run_command_with_status(ssh, command)
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'Environment Setup Completed' in line:
                return True
    return False