import logging
import os
from urlparse import urlparse, parse_qsl

from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection
from bdphpcprovider.smartconnectorscheduler.sshconnector import run_sudo_command
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientResourceError
from bdphpcprovider.smartconnectorscheduler.stages.errors import MissingConfigurationError
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.errors import deprecated

logger = logging.getLogger(__name__)


@deprecated
class Setup(Stage):
    """
    Handles creation of a running executable on the VMS in a group
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.group_id = ''
        self.platform = None
        # We want to isolate all the botoconnector methods from run_settings structure, so
        # build dict to hold user_settings plus needed values.
        self.boto_settings = user_settings.copy()
        logger.debug('Setup initialised')

    def triggered(self, run_settings):
        """
        Triggered if appropriate vms exist and we have not finished setup
        """

        try:
            self.group_id = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/create/group_id')
        except KeyError:
            logger.warn("no group_id found in context")
            return False

        logger.debug("group_id = %s" % self.group_id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/setup',
            u'setup_finished'):
            logger.debug(run_settings[
                'http://rmit.edu.au/schemas/stages/setup'][u'setup_finished'])
            logger.warn("setup_finished exists")
            # TODO: check whether number of setup_nodes equals number_vm_instances
            # otherwise retry this method to allocate rest
            return False

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/vm_image')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/vm_size')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/security_group')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/group_id_dir')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')

        self.boto_settings['username'] = \
            run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['password'] = \
            run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
        key_file = hrmcstages.retrieve_private_key(self.boto_settings, self.user_settings['nectar_private_key'])
        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file

        self.packaged_nodes = botocloudconnector.get_rego_nodes(
            self.boto_settings)
        logger.debug("packaged_nodes = %s" % self.packaged_nodes)

        logger.debug("Setup on %s" % run_settings['http://rmit.edu.au/schemas/system']['platform'])
        return len(self.packaged_nodes)

    def process(self, run_settings):
        """
        Setup all the nodes
        """
        self.setup(self.boto_settings, self.group_id)
        logger.debug('Setup finished')

    def output(self, run_settings):
        """
        Store number of packages nodes as setup_finished in runinfo.sys
        """
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/setup',
            {})[u'setup_finished'] = len(self.packaged_nodes)
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/system/misc',
            {})[u'id'] = 0

        # FIXME: probably should be set at beginning of run or connector?
        #update_key('id', 0, context)
        logger.debug('Setup output returned')
        return run_settings

    def setup(self, settings, group_id, maketarget_nodegroup_pair={}):
        available_nodes = list(botocloudconnector.get_rego_nodes(settings))
        requested_nodes = 0

        if 'payload_source' not in settings:
            message = "payload_source is not set"
            logger.exception(message)
            raise MissingConfigurationError(message)

        if 'payload_destination' not in settings:
            message = "payload_destination is not set"
            logger.exception(message)
            raise MissingConfigurationError(message)

        if not maketarget_nodegroup_pair:
            EMPTY_MAKE_TARGET = ''
            requested_nodes = len(available_nodes)
            maketarget_nodegroup_pair[EMPTY_MAKE_TARGET] = requested_nodes
        else:
            for i in maketarget_nodegroup_pair.keys():
                requested_nodes += maketarget_nodegroup_pair[i]
            if requested_nodes > len(available_nodes):
                message = "Requested nodes %d; but available nodes %s " \
                    % (requested_nodes, len(available_nodes))
                logger.exception(message)
                raise InsufficientResourceError(message)
        logger.info("Requested nodes %d: \nAvailable nodes %s "
               % (requested_nodes, len(available_nodes)))

        def setup_worker(node_ip, make_target, source, destination):
            logger.info("Setting up node with IP %s using makefile %s" \
                % (node_ip, make_target))
            self.setup_task(settings, node_ip, make_target, source, destination)
            logger.info("Setting up machine with IP %s completed" % node_ip)

        import threading
        threads_running = []
        for make_target in maketarget_nodegroup_pair:
            for i in range(0, maketarget_nodegroup_pair[make_target]):
                logger.debug("starting thread")
                instance = available_nodes[0]
                node_ip = botocloudconnector.get_instance_ip(instance.id, settings)

                source = smartconnector.get_url_with_pkey(settings, settings['payload_source'])
                relative_path = settings['platform'] + '@' + settings['payload_destination']
                destination = smartconnector.get_url_with_pkey(settings, relative_path,
                                                     is_relative_path=True,
                                                     ip_address=node_ip)
                logger.debug("Source %s" % source)
                logger.debug("Destination %s" % destination)
                logger.debug("Relative path %s" % relative_path)
                t = threading.Thread(target=setup_worker,
                    args=(node_ip, make_target, source, destination))
                threads_running.append(t)
                t.start()
                available_nodes.pop(0)

        for thread in threads_running:
            logger.debug("waiting on thread")
            # TODO FIXME: need to look carefully at hanging where single task does not finish.  Need a
            # timeout to restart the process.
            t.join()
        logger.debug("all threads are done")

    def setup_task(self, settings, node_ip, make_target, source, destination):
        """
        Transfer the task package to the node and install
        """
        hrmcstages.copy_directories(source, destination)
        # FIXME: if any problems with copy_directive, exit but don't set setup_finished.
        makefile_path = self.get_make_path(destination)
        # Check whether make is installed. If not install
        check_make_installation = '`command -v make  > /dev/null 2>&1 || echo sudo yum install -y make`; '
        execute_setup = "cd %s; make %s " % (makefile_path, make_target)
        command = check_make_installation + execute_setup
        logger.debug("Setting up environment using makefile with target %s" % make_target)
        logger.info("Setup node with IP %s" % node_ip)
        ssh = open_connection(ip_address=node_ip, settings=settings)
        #run_sudo_command(ssh, command, settings, "")
        sshconnector.run_command_with_tty(ssh, command, settings)

    def get_make_path(self, destination):
        """
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
