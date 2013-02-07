from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection
from bdphpcprovider.smartconnectorscheduler.sshconnector import put_payload
from bdphpcprovider.smartconnectorscheduler.sshconnector import run_sudo_command
from bdphpcprovider.smartconnectorscheduler.sshconnector import mkdir

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_run_settings
from bdphpcprovider.smartconnectorscheduler.hrmcstages import update_key


import os
import logging

logger = logging.getLogger(__name__)


class InsufficientResourceError(Exception):
    pass


class Setup(Stage):
    """
    Handles creation of a running executable on the VMS in a group
    """

    def __init__(self):
        self.settings = {}
        self.group_id = ''


    def triggered(self, context):
        """
        Triggered if appropriate vms exist and we have not finished setup
        """
        # triggered if the set of the VMS has been established.
        self.settings = get_run_settings(context)
        #logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        if 'setup_finished' in self.settings:
            return False

        self.packaged_nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
        logger.debug("packaged_nodes = %s" % self.packaged_nodes)

        logger.debug("Setup on %s" % self.settings['PROVIDER'])
        return len(self.packaged_nodes)


    def process(self, context):
        """
        Setup all the nodes
        """
        #setup_multi_task(self.group_id, self.settings)
        self.setup(self.settings, self.group_id)


    def output(self, context):
        """
        Store number of packages nodes as setup_finished in runinfo.sys
        """
        update_key('setup_finished', len(self.packaged_nodes), context)
        # So initial input goes in input_0 directory
        update_key('id', 0, context)

        return context


    def setup(self, settings, group_id, maketarget_nodegroup_pair={}):
        available_nodes = list(botocloudconnector.get_rego_nodes(group_id, settings))
        requested_nodes=0

        if not maketarget_nodegroup_pair:
            EMPTY_MAKE_TARGET = ''
            requested_nodes = len(available_nodes)
            maketarget_nodegroup_pair[EMPTY_MAKE_TARGET] = requested_nodes
        else:
            for i in maketarget_nodegroup_pair:
                requested_nodes += maketarget_nodegroup_pair[i]
            if requested_nodes > len(available_nodes):
                logger.exception("Requested nodes %d; but available nodes %s "
                                   % (requested_nodes, len(available_nodes)))
                raise InsufficientResourceError
        logger.info("Requested nodes %d: \nAvailable nodes %s "
               % (requested_nodes, len(available_nodes)))

        def setup_worker(node_ip, make_target):
            logger.info("Setting up node with IP %s using makefile %s"
                        %(node_ip, make_target))
            self.setup_task(settings, node_ip, make_target)
            logger.info("Setting up machine with IP %s completed" % node_ip)

        import threading
        threads_running = []
        for make_target in maketarget_nodegroup_pair:
            for i in range(0, maketarget_nodegroup_pair[make_target]):
                logger.debug("starting thread")
                instance = available_nodes[0]
                node_ip = botocloudconnector.get_instance_ip(instance.id, settings)
                t = threading.Thread(target=setup_worker,
                    args=(node_ip, make_target))
                threads_running.append(t)
                t.start()
                available_nodes.pop(0)

        for thread in threads_running:
            logger.debug("waiting on thread")
            t.join()
        logger.debug("all threads are done")


    def setup_task(self, settings, node_ip, make_target):
        """
        Transfer the task package to the node and install
        """
        logger.info("Setup node with IP %s" % node_ip)
        ssh = open_connection(ip_address=node_ip, settings=settings)
        logger.debug("Setup %s ssh" % ssh)

        source = settings['PAYLOAD_SOURCE']
        destination = settings['PAYLOAD_DESTINATION']

        mkdir(ssh, destination)
        put_payload(ssh, source, destination)

        makefile_path = settings['PAYLOAD_DESTINATION']
       # Check whether make is installed. If not install
        check_make_installation = '`command -v make  > /dev/null 2>&1 || echo sudo yum install -y make`; '
        execute_setup =  "cd %s; make %s " % (makefile_path, make_target)
        command = check_make_installation + execute_setup
        logger.debug("Setting up environment using makefile with target %s" % make_target)
        run_sudo_command(ssh, command, settings, "")