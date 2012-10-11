import os
import logging

from sshconnector import open_connection
from sshconnector import run_command
from sshconnector import install_deps
from sshconnector import unpack
from sshconnector import compile
from sshconnector import mkdir
from sshconnector import get_file
from sshconnector import put_file
from sshconnector import get_package_pids

from cloudconnector import is_instance_running
from cloudconnector import get_rego_nodes
from cloudconnector import get_instance_ip

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class PackageFailedError(Error):
    pass


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


def prepare_input(instance_id, input_dir, settings, seed):
    """
        Take the input_dir and move all the contained files to the
        instance and ready

    """
    logger.info("prepare_input %s %s" % (instance_id, input_dir))
    ip = get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    input_dir = _normalize_dirpath(input_dir)
    dirList = os.listdir(input_dir)
    for fname in dirList:
        logger.debug(fname)
        _upload_input(ssh, input_dir, fname,
                      os.path.join(settings['DEST_PATH_PREFIX'],
                                   settings['PAYLOAD_CLOUD_DIRNAME']))
    run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))


def run_task(instance_id, settings):
    """
        Start the task on the instance, then hang and
        periodically check its state.
    """
    logger.info("run_task %s" % instance_id)
    ip = get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip,
                          settings=settings)
    pids = get_package_pids(ssh, settings['COMPILE_FILE'])
    logger.debug("pids=%s" % pids)
    if len(pids) > 1:
        logger.error("warning:multiple packages running")
        raise PackageFailedError("multiple packages running")
    run_command(ssh, "cd %s; ./%s >& %s &\
    " % (os.path.join(settings['DEST_PATH_PREFIX'],
                      settings['PAYLOAD_CLOUD_DIRNAME']),
         settings['COMPILE_FILE'], "output"))

    import time
    attempts = settings['RETRY_ATTEMPTS']
    logger.debug("checking for package start")
    for x in range(0, attempts):
        time.sleep(5)  # to give process enough time to start
        pids = get_package_pids(ssh, settings['COMPILE_FILE'])
        logger.debug("pids=%s" % pids)
        if pids:
            break
    else:
        raise PackageFailedError("package did not start")
    # pids should have maximum of one element
    return pids


def get_output(instance_id, output_dir, settings):
    """
        Retrieve the output from the task on the node
    """
    logger.info("get_output %s" % instance_id)
    ip = get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    try:
        os.makedirs(output_dir)  # NOTE: makes intermediate directories
    except OSError, e:
        logger.debug("output directory %s already exists: %s\
        " % (output_dir, e))
        #sys.exit(1)
    logger.info("output directory is %s" % output_dir)
    for file in settings['OUTPUT_FILES']:
        get_file(ssh, os.path.join(settings['DEST_PATH_PREFIX'],
                                   settings['PAYLOAD_CLOUD_DIRNAME']),
                 file, output_dir)
    # TODO: do integrity check on output files
    pass


def job_finished(instance_id, settings):
    """
        Return True if package job on instance_id has job_finished
    """
    ip = get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    pids = get_package_pids(ssh, settings['COMPILE_FILE'])
    logger.debug("pids=%s" % repr(pids))
    return pids == [""]


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
        t = threading.Thread(target=setup_worker, args=(node.id,))
        threads_running.append(t)
        t.start()
    for thread in threads_running:
        logger.debug("waiting on thread")
        t.join()
    logger.debug("all threads are done")


def packages_complete(group_id, output_dir, settings):
    """
    Indicates if all the package nodes have finished and generate
    any output as needed
    """
    nodes = get_rego_nodes(group_id, settings)
    error_nodes, finished_nodes = _status_of_nodeset(nodes,
                                                     output_dir,
                                                     settings)
    if finished_nodes + error_nodes == nodes:
        logger.info("Package Finished")
        return True

    if error_nodes:
        logger.warn("error nodes: %s" % error_nodes)
        return True

    return False


def run_multi_task(group_id, output_dir, settings):
    """
    Run the package on each of the nodes in the group and grab
    any output as needed
    """
    nodes = get_rego_nodes(group_id, settings)

    pids = []
    for node in nodes:
        try:
            pids_for_task = run_task(node.id, settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start package on node %s" % node)
            #TODO: cleanup node of copied input files etc.
        else:
            pids.append(pids_for_task)

    all_pids = dict(zip(nodes, pids))
    return all_pids


def prepare_multi_input(group_id, input_dir, settings, seed):
    """
        Take the input_dir and move all the contained files to the
        instances in the group and ready

    """
    nodes = get_rego_nodes(group_id, settings)

    import random
    random.seed(seed)
    seeds = {}
    for node in nodes:
        # FIXME: is the random supposed to be positive or negative?
        seeds[node] = random.randrange(0, settings['MAX_SEED_INT'])

    if seed:
        print ("seed for full package run = %s" % seed)
    else:
        print ("seeds for each node in group %s = %s\
        " % (group_id, [(x.id, seeds[x]) for x in seeds.keys()]))

    logger.debug("seeds = %s" % seeds)
    for node in nodes:
        instance_id = node.id
        logger.info("prepare_input %s %s" % (instance_id, input_dir))
        ip = get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip, settings=settings)
        input_dir = _normalize_dirpath(input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:
            logger.debug(fname)
            _upload_input(ssh, input_dir, fname,
                          os.path.join(settings['DEST_PATH_PREFIX'],
                                       settings['PAYLOAD_CLOUD_DIRNAME']))
        run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))

        run_command(ssh,
                    "cd %s; sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' rmcen.inp\
                    " % (os.path.join(settings['DEST_PATH_PREFIX'],
                                      settings['PAYLOAD_CLOUD_DIRNAME']),
                         seeds[node]))


#should remove this directory
def _upload_input(ssh, source_path_prefix, input_file, dest_path_prefix):
        put_file(ssh, source_path_prefix, input_file, dest_path_prefix)


#TODO: move this method to utility
def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath


def _status_of_nodeset(nodes, output_dir, settings):
    """
    Return lists that describe which of the set of nodes are finished or
    have disappeared
    """
    error_nodes = []
    finished_nodes = []

    for node in nodes:
        instance_id = node.id
        if not is_instance_running(instance_id, settings):
            # An unlikely situation where the node crashed after is was
            # detected as registered.
            logging.error('Instance %s not running' % instance_id)
            error_nodes.append(node)
            continue
        if job_finished(instance_id, settings):
            print "done. output is available"
            get_output(instance_id,
                       "%s/%s" % (output_dir, node.id),
                       settings)
            finished_nodes.append(node)
        else:
            print "job still running on %s: %s\
            " % (instance_id, get_instance_ip(instance_id, settings))

    return (error_nodes, finished_nodes)
