from botocloudconnector import get_rego_nodes
from botocloudconnector import get_instance_ip

from sshconnector import open_connection
from sshconnector import put_payload
from sshconnector import run_sudo_command
from sshconnector import mkdir

import os
import logging

logger = logging.getLogger(__name__)


def setup(settings, group_id, node_config_list, node_group_list=[]):
    available_nodes = get_rego_nodes(group_id, settings)
    requested_nodes=0

    if not node_group_list:
        node_group_list.append(len(available_nodes))
        for i in node_group_list:
            requested_nodes+=i
    else:
        pass

    print ("Requested nodes %d: \nAvailable nodes %s "
           % (requested_nodes, len(available_nodes)))

    if requested_nodes > len(available_nodes):
        logger.info("Requested nodes is more than available nodes")
        return



    def setup_worker(node_ip, config_file):
        logger.info("Setting up node with IP %s using makefile %s"
                    %(node_ip, config_file))
        setup_task(settings, node_ip, config_file)
        logger.info("Setting up machine with IP %s completed"
                    %(node_ip, config_file))

    import threading
    threads_running = []
    index = 0
    for config_file in node_config_list:
        for i in range(0, node_group_list[index]):
            logger.debug("starting thread")
            instance = available_nodes[0]
            node_ip = get_instance_ip(instance.id, settings)
            t = threading.Thread(target=setup_worker,
                args=(node_ip, config_file))
            threads_running.append(t)
            t.start()
            available_nodes.pop(0)

    for thread in threads_running:
        logger.debug("waiting on thread")
        t.join()
    logger.debug("all threads are done")


def setup_task(settings, node_ip, config_file):
    """
    Transfer the task package to the node and install
    """
    logger.info("Setup node with IP %s" % node_ip)
    ssh = open_connection(ip_address=node_ip, settings=settings)
    logger.debug("Setup %s ssh" % ssh)

    source = settings['PAYLOAD_SOURCE']
    destination = settings['PAYLOAD_DESTINATION']
    if destination:
        mkdir(ssh, destination)
    put_payload(ssh, source, destination)

    makefile = os.path.join(settings['PAYLOAD_DESTINATION'],
        settings['PAYLOAD_NAME'], config_file)
    command = "make -f %s " % makefile
    logger.debug("Setting up environment using makefile %s" % makefile)
    run_sudo_command(ssh, command, settings, "")










'''
def setup_multi_task(group_id, settings):
    """
    Transfer the task package to the instances in group_id and install
    """
    logger.info("setup_multi_task %s " % group_id)
    packaged_nodes = get_rego_nodes(group_id, settings)
    import threading
    import datetime
    logger.debug("packaged_nodes = %s" % packaged_nodes)

    def setup_worker(node_id):
        now = datetime.datetime.now()
        logger.debug("%s says Hello World at time: %s" % (node_id, now))
        # TODO: need to make sure that setup_task eventually finishes
        logger.debug("about to start setup_task")
        setup_task(node_id, settings)
        logger.debug("setup finished")

    threads_running = []
    for node in packaged_nodes:
        logger.debug("starting thread")
        instance_id = node.id
        t = threading.Thread(target=setup_worker, args=(instance_id,))
        threads_running.append(t)
        t.start()
    for thread in threads_running:
        logger.debug("waiting on thread")
        t.join()
    logger.debug("all threads are done")


'''

'''
def setup_task(instance_id, settings):
    """
    Transfer the task package to the node and install
    """

    logger.info("setup_task %s " % instance_id)

    ip = get_instance_ip(instance_id, settings)
    logger.debug("Setup %s IP" % ip)
    ssh = open_connection(ip_address=ip, settings=settings)
    logger.debug("Setup %s ssh" % ssh)

    res = install_deps(ssh, packages=settings['DEPENDS'],
        settings=settings, instance_id=instance_id)
    logger.debug("install res=%s" % res)
    res = mkdir(ssh, dir=settings['DEST_PATH_PREFIX'])
    logger.debug("mkdir res=%s" % res)
    put_file(ssh,
        source_path=settings['PAYLOAD_LOCAL_DIRNAME'],
        package_file=settings['PAYLOAD'],
        environ_dir=settings['DEST_PATH_PREFIX'])

    unpack(ssh, environ_dir=settings['DEST_PATH_PREFIX'],
        package_file=settings['PAYLOAD'])

    compile(ssh, environ_dir=settings['DEST_PATH_PREFIX'],
        compile_file=settings['COMPILE_FILE'],
        package_dirname=settings['PAYLOAD_CLOUD_DIRNAME'],
        compiler_command=settings['COMPILER'])

    res = mkdir(ssh,
        dir=settings['POST_PROCESSING_DEST_PATH_PREFIX'])



    post_processing_dest = os.path.join(settings['POST_PROCESSING_DEST_PATH_PREFIX'],
        settings['POST_PAYLOAD_CLOUD_DIRNAME'])
    res = mkdir(ssh, dir=post_processing_dest)

    logger.debug("mkdir res=%s" % res)
    logger.debug("Post Processing === %s" % post_processing_dest)
    put_file(ssh,
        source_path=settings['POST_PROCESSING_LOCAL_PATH'],
        package_file=settings['POST_PAYLOAD'],
        environ_dir=settings['POST_PROCESSING_DEST_PATH_PREFIX'])

    zipped =os.path.join(settings['POST_PROCESSING_DEST_PATH_PREFIX'],
        settings['POST_PAYLOAD'])
    unzip(ssh, zipped_file=zipped,
        destination_dir=post_processing_dest)

    compile(ssh, environ_dir=settings['POST_PROCESSING_DEST_PATH_PREFIX'],
        compile_file=settings['POST_PAYLOAD_COMPILE_FILE'],
        package_dirname=settings['POST_PAYLOAD_CLOUD_DIRNAME'],
        compiler_command=settings['COMPILER'])
'''