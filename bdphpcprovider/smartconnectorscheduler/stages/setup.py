from botocloudconnector import get_rego_nodes
from botocloudconnector import get_instance_ip

from sshconnector import open_connection
from sshconnector import put_payload
from sshconnector import run_sudo_command
from sshconnector import mkdir

import os
import logging

logger = logging.getLogger(__name__)



class InsufficientResourceError(Exception):
    pass

EMPTY_MAKE_TARGET = ''

def setup(settings, group_id, maketarget_nodegroup_pair={}):
    available_nodes = get_rego_nodes(group_id, settings)
    requested_nodes=0

    if not maketarget_nodegroup_pair:
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
        setup_task(settings, node_ip, make_target)
        logger.info("Setting up machine with IP %s completed" % node_ip)

    import threading
    threads_running = []
    for make_target in maketarget_nodegroup_pair:
        for i in range(0, maketarget_nodegroup_pair[make_target]):
            logger.debug("starting thread")
            instance = available_nodes[0]
            node_ip = get_instance_ip(instance.id, settings)
            t = threading.Thread(target=setup_worker,
                args=(node_ip, make_target))
            threads_running.append(t)
            t.start()
            available_nodes.pop(0)

    for thread in threads_running:
        logger.debug("waiting on thread")
        t.join()
    logger.debug("all threads are done")


def setup_task(settings, node_ip, make_target):
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

    for root, dirs, files in os.walk(source):
        payload_top_dir = os.path.basename(root)
        break

    makefile_path = os.path.join(settings['PAYLOAD_DESTINATION'],
        payload_top_dir)

    # Check whether make is installed. If not install
    check_make_installation = '`command -v make  > /dev/null 2>&1 || echo sudo yum install -y make`; '
    execute_setup =  "cd %s; make %s " % (makefile_path, make_target)
    command = check_make_installation + execute_setup
    logger.debug("Setting up environment using makefile with taget %s" % make_target)
    run_sudo_command(ssh, command, settings, "")