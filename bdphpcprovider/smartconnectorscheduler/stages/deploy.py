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
import time
import ast
import os
from urlparse import urlparse, parse_qsl


from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection
from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientResourceError


logger = logging.getLogger(__name__)


class Deploy(Stage):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.job_dir = "hrmcrun"
        self.boto_settings = user_settings.copy()

    def triggered(self, run_settings):

        try:
            self.group_id = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/create/group_id')
        except KeyError:
            logger.warn("no group_id found in context")
            return False

        try:
            number_vm_instances = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        except KeyError:
            logger.error("no number_vm_instances found in context")
            return False

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/deploy',
            u'deployed_nodes'):
            deploy_str = run_settings['http://rmit.edu.au/schemas/stages/deploy'][u'deployed_nodes']
            self.deployed_nodes = ast.literal_eval(deploy_str)
            return len(self.deployed_nodes) < number_vm_instances
        else:
            self.deployed_nodes = []
            return True

        return False

    def process(self, run_settings):

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/deploy',
            u'started'):
            self.started = int(run_settings['http://rmit.edu.au/schemas/stages/deploy'][u'started'])
        else:
            self.started = 0

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/created_nodes')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/group_id_dir')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/created_nodes')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')
        self.boto_settings['username'] = \
            run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['username'] = 'root'  # FIXME: schema value is ignored
        self.boto_settings['password'] = \
            run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
        key_file = hrmcstages.retrieve_private_key(self.boto_settings, self.user_settings['nectar_private_key'])
        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file

        if not self.started:
            try:
                _ = start_multi_setup_task(self.group_id,
                                           self.boto_settings)
            except PackageFailedError, e:
                logger.error("unable to start setup of packages: %s" % e)
            pass
            self.started = 1
        else:
            self.nodes = botocloudconnector.get_rego_nodes(self.group_id,
                self.boto_settings)
            self.error_nodes = []
            for node in self.nodes:
                #ip = botocloudconnector.get_instance_ip(node.id, self.boto_settings)
                #ssh = open_connection(ip_address=ip, settings=self.boto_settings)
                if not botocloudconnector.is_instance_running(node.id,
                     self.boto_settings):
                    # An unlikely situation where the node crashed after is was
                    # detected as registered.
                    #FIXME: should error nodes be counted as finished?
                    logging.error('Instance %s not running' % node.id)
                    self.error_nodes.append(node)
                    continue

                node_ip = botocloudconnector.get_instance_ip(node.id,
                    self.boto_settings)
                relative_path = "%s@%s" % (self.boto_settings['platform'],
                    self.boto_settings['payload_destination'])
                destination = smartconnector.get_url_with_pkey(self.boto_settings,
                    relative_path,
                    is_relative_path=True,
                    ip_address=node_ip)
                logger.debug("Relative path %s" % relative_path)
                logger.debug("Destination %s" % destination)
                fin = job_finished(node.id, node_ip, self.boto_settings, destination)
                logger.debug("fin=%s" % fin)
                if fin:
                    print "done. output is available"
                    logger.debug("node=%s" % str(node))
                    logger.debug("deployed_nodes=%s" % self.deployed_nodes)
                    if not (node.id in [x for x in self.deployed_nodes]):
                        self.deployed_nodes.append(node.id)
                    else:
                        logger.info("We have already "
                            + "processed output from node %s" % node.id)
                else:
                    print "job still running on %s: %s\
                    " % (node.id,
                         botocloudconnector.get_instance_ip(node.id, self.boto_settings))

    def output(self, run_settings):

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/deploy',
            {})[u'started'] = self.started

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/deploy',
            {})[u'deployed_nodes'] = str(self.deployed_nodes)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/system/misc',
            {})[u'id'] = 0


        return run_settings


def job_finished(instance_id, ip, settings, destination):
    """
        Return True if package job on instance_id has job_finished
    """
    ssh = open_connection(ip_address=ip, settings=settings)
    makefile_path = get_make_path(destination)
    command = "cd %s; make %s" % (makefile_path, 'setupdone')
    command_out, _ = sshconnector.run_command_with_status(ssh, command)
    if command_out:
        logger.debug("command_out = %s" % command_out)
        for line in command_out:
            if 'Deployment Completed' in line:
                return True
    return False


def start_setup(instance, ip,  settings, source, destination):
    """
        Start the task on the instance, then return
    """
    logger.info("run_task %s" % str(instance))

    hrmcstages.copy_directories(source, destination)
    makefile_path = get_make_path(destination)

    # TODO, FIXME:  need to have timeout for yum install make
    # and then test can access, otherwise, loop.

    check_make_installation = 'yum install -y make'

    curr_username = settings['username']
    settings['username'] = 'root'
    command_out = ''
    errs = ''
    logger.debug("starting command for %s" % ip)
    try:
        ssh = open_connection(ip_address=ip, settings=settings)
        command_out, errs = sshconnector.run_command_with_status(ssh, check_make_installation)
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
        ssh = open_connection(ip_address=ip, settings=settings)
        command_out, errs = sshconnector.run_command_with_status(ssh, command)
    except Exception, e:
        logger.error(e)
    finally:
        if ssh:
            ssh.close()
    logger.debug("command_out2=(%s, %s)" % (command_out, errs))

    settings['username'] = curr_username


def get_make_path(destination):
    """
    TODO: move this into hrmcstages?
    """
    destination = hrmcstages.get_http_url(destination)
    url = urlparse(destination)
    query = parse_qsl(url.query)
    query_settings = dict(x[0:] for x in query)
    path = url.path
    if path[0] == os.path.sep:
        path = path[1:]
    make_path = os.path.join(query_settings['root_path'], path)
    logger.debug("Makefile path %s %s %s " % (make_path, query_settings['root_path'], path))
    return make_path


def start_multi_setup_task(group_id, settings, maketarget_nodegroup_pair={}):
    """
    Run the package on each of the nodes in the group and grab
    any output as needed
    """

    nodes = botocloudconnector.get_rego_nodes(group_id, settings)
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

    for make_target in maketarget_nodegroup_pair:
        for i in range(0, maketarget_nodegroup_pair[make_target]):
            instance = nodes[0]
            logger.debug("instance.id=%s" % str(instance.id))
            logger.debug("instance.ip=%s" % str(instance.ip))
            logger.debug("instance=%s" % str(instance))
            node_ip = botocloudconnector.get_instance_ip(instance.id, settings)
            logger.debug("node_ip=%s"  % node_ip)
            source = smartconnector.get_url_with_pkey(settings, settings['payload_source'])
            relative_path = settings['platform'] + '@' + settings['payload_destination']
            destination = smartconnector.get_url_with_pkey(settings, relative_path,
                                                 is_relative_path=True,
                                                 ip_address=node_ip)
            logger.debug("Source %s" % source)
            logger.debug("Destination %s" % destination)
            logger.debug("Relative path %s" % relative_path)

            start_setup(instance, node_ip, settings, source, destination)
            nodes.pop(0)
