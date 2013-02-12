import os
import logging

from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection, run_command, install_deps, unpack, unzip, compile, mkdir, get_file, put_file
from bdphpcprovider.smartconnectorscheduler.sshconnector import get_package_pids
from bdphpcprovider.smartconnectorscheduler.sshconnector import find_remote_files
from bdphpcprovider.smartconnectorscheduler import botocloudconnector

logger = logging.getLogger(__name__)


class Error(Exception):
    pass




def setup_task(instance_id, settings):
    """
    Transfer the task package to the node and install
    """

    logger.info("setup_task %s " % instance_id)

    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    logger.debug("Setup %s IP" % ip)
    ssh = open_connection(ip_address=ip, settings=settings)
    logger.debug("Setup %s ssh" % ssh)

    res = install_deps(ssh, packages=settings['DEPENDS'],
                       settings=settings, instance_id=instance_id)
    logger.debug("install res=%s" % res)
    res = mkdir(ssh, dir=settings['PAYLOAD_DESTINATION'])
    logger.debug("mkdir res=%s" % res)
    put_file(ssh,
             source_path=settings['PAYLOAD_LOCAL_DIRNAME'],
             package_file=settings['PAYLOAD'],
             environ_dir=settings['PAYLOAD_DESTINATION'])

    unpack(ssh, environ_dir=settings['PAYLOAD_DESTINATION'],
           package_file=settings['PAYLOAD'])

    compile(ssh, environ_dir=settings['PAYLOAD_DESTINATION'],
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



def prepare_input(instance_id, input_dir, settings, seed):
    """
        Take the input_dir and move all the contained files to the
        instance and ready

    """
    logger.info("prepare_input %s %s" % (instance_id, input_dir))
    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    input_dir = _normalize_dirpath(input_dir)
    dirList = os.listdir(input_dir)
    for fname in dirList:
        logger.debug(fname)
        _upload_input(ssh, input_dir, fname,
                      os.path.join(settings['PAYLOAD_DESTINATION'],
                                   settings['PAYLOAD_CLOUD_DIRNAME']))
    run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                (os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                (os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                (os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))


def get_output_old(instance_id, output_dir, settings):
    """
        Retrieve the output from the task on the node
    """
    logger.info("get_output %s" % instance_id)
    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    directory_created = False
    while not directory_created:
        try:
            os.makedirs(output_dir)  # NOTE: makes intermediate directories
            directory_created = True
        except OSError, e:
            logger.debug("output directory %s already exists: %s Deleting the existing directory ...\
                         " % (output_dir, output_dir))
            import shutil
            shutil.rmtree(output_dir)
            logger.debug("Existing directory %s along with its previous content deleted" % output_dir)
            logger.debug("Empty directory %s created" % output_dir)
            #sys.exit(1)
    logger.info("output directory is %s" % output_dir)
    cloud_path = os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])
    remote_files = [os.path.basename(x) for x in find_remote_files(ssh,
                                                                   cloud_path)]
    logger.debug("remote_files=%s" % remote_files)
    for file in remote_files:
        get_file(ssh, os.path.join(settings['PAYLOAD_DESTINATION'],
                                   settings['PAYLOAD_CLOUD_DIRNAME']),
                 file, output_dir)
    # TODO: do integrity check on output files
    pass

from stat import S_ISDIR


def isdir(sftp, path):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        #Path does not exist, so by definition not a directory
        return False


def _get_paths(sftp, dir):
    file_list = sftp.listdir(path=dir)
    logger.debug("file_qlist=%s" % file_list)
    dirs = []
    for item in file_list:
        if isdir(sftp, str(item)):
            p = _get_paths(sftp, item)
            for x in p:
                dirs.append(x)
        else:
            dirs.append(item)
    return dirs


def get_output(fs, instance_id, output_dir, settings):
    """
        Retrieve the output from the task on the node
    """
    logger.info("get_output %s" % instance_id)
    output_dir = os.path.join(fs, fs.get_global_filesystem(),
                                   output_dir,
                                   instance_id)
    logger.debug("new output_dir = %s" % output_dir)
    directory_created = False
    while not directory_created:
        try:
            os.makedirs(output_dir)  # NOTE: makes intermediate directories
            directory_created = True
        except OSError, e:
            logger.debug("output directory %s already exists: %s Deleting the existing directory ...\
                         " % (output_dir, output_dir))
            import shutil
            shutil.rmtree(output_dir)
            logger.debug("Existing directory %s along with its previous content deleted" % output_dir)
            logger.debug("Empty directory %s created" % output_dir)
            #sys.exit(1)
    logger.info("output directory is %s" % output_dir)

    cloud_path = os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])
    logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    ftp = ssh.open_sftp()
    cloud_path = os.path.join(settings['PAYLOAD_DESTINATION'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])
    logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
    paths = _get_paths(ftp, cloud_path)
    logger.debug("paths = %s" % paths)

    for p in paths:
        ftp.get(os.path.join(cloud_path, p), os.path.join(output_dir, p))

    ftp.close()
    ssh.close()


def get_post_output(instance_id, output_dir, settings):
    """
        Retrieve the output from the task on the node
    """
    logger.info("get_post_output %s" % instance_id)
    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip, settings=settings)
    try:
        os.makedirs(output_dir)  # NOTE: makes intermediate directories
    except OSError, e:
        logger.debug("output directory %s already exists: %s\
        " % (output_dir, e))
        #sys.exit(1)
    logger.info("output directory is %s" % output_dir)
    cloud_path = os.path.join(settings['POST_PROCESSING_DEST_PATH_PREFIX'],
        settings['POST_PAYLOAD_CLOUD_DIRNAME'])
    remote_files = [os.path.basename(x) for x in find_remote_files(ssh,
        cloud_path)]
    logger.debug("remote_files=%s" % remote_files)
    for file in remote_files:
        get_file(ssh, os.path.join(settings['POST_PROCESSING_DEST_PATH_PREFIX'],
            settings['POST_PAYLOAD_CLOUD_DIRNAME']),
            file, output_dir)
        # TODO: do integrity check on output files
    pass



def setup_multi_task(group_id, settings):
    """
    Transfer the task package to the instances in group_id and install
    """
    logger.info("setup_multi_task %s " % group_id)
    packaged_nodes = botocloudconnector.get_rego_nodes(group_id, settings)
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


# def packages_complete(group_id, output_dir, settings):
#     """
#     Indicates if all the package nodes have finished and generate
#     any output as needed
#     """
#     nodes = botocloudconnector.get_rego_nodes(group_id, settings)
#     error_nodes, finished_nodes = _status_of_nodeset(nodes,
#                                                      output_dir,
#                                                      settings)
#     if finished_nodes + error_nodes == nodes:
#         logger.info("Package Finished")
#         return True

#     if error_nodes:
#         logger.warn("error nodes: %s" % error_nodes)
#         return True

#     return False


def prepare_multi_input(group_id, input_dir, settings, seed):
    """
        Take the input_dir and move all the contained files to the
        instances in the group and ready

    """
    nodes = botocloudconnector.get_rego_nodes(group_id, settings)

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
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip, settings=settings)
        input_dir = _normalize_dirpath(input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:
            logger.debug(fname)
            _upload_input(ssh, input_dir, fname,
                          os.path.join(settings['PAYLOAD_DESTINATION'],
                                       settings['PAYLOAD_CLOUD_DIRNAME']))

        run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                    (os.path.join(settings['PAYLOAD_DESTINATION'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                    (os.path.join(settings['PAYLOAD_DESTINATION'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                    (os.path.join(settings['PAYLOAD_DESTINATION'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        run_command(ssh, "cd %s;\
                    sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' rmcen.inp\
                    " % (os.path.join(settings['PAYLOAD_DESTINATION'],
                                      settings['PAYLOAD_CLOUD_DIRNAME']),
                         seeds[node]))


        post_processing_dest = os.path.join(
            settings['POST_PROCESSING_DEST_PATH_PREFIX'],
            settings['POST_PAYLOAD_CLOUD_DIRNAME'])

        run_command(ssh, "cd %s; cp PSD.inp PSD.inp.orig" %
                         post_processing_dest)
        run_command(ssh, "cd %s; dos2unix PSD.inp" %
                         post_processing_dest)
        run_command(ssh, "cd %s; sed -i '/^$/d' PSD.inp" %
                         post_processing_dest)
        run_command(ssh, "cd %s;\
                    sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' PSD.inp\
                    " % (post_processing_dest,
                         seeds[node]))



#should remove this directory
def _upload_input(ssh, source_path_prefix, input_file, dest_path_prefix):
        put_file(ssh, source_path_prefix, input_file, dest_path_prefix)


#TODO: move this method to utility
def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath



# def _status_of_nodeset(nodes, output_dir, settings):
#     """
#     Return lists that describe which of the set of nodes are finished or
#     have disappeared
#     """
#     error_nodes = []
#     finished_nodes = []

#     for node in nodes:
#         instance_id = node.id

#         if not botocloudconnector.is_instance_running(instance_id, settings):
#             # An unlikely situation where the node crashed after is was
#             # detected as registered.
#             logging.error('Instance %s not running' % instance_id)
#             error_nodes.append(node)
#             continue

#         finished = Fin()
#         if finished.job_finished(instance_id, settings):
#             print "done. output is available"
#             get_output(instance_id,
#                        "%s/%s" % (output_dir, instance_id),
#                        settings)

#             run_post_task(instance_id, settings)
#             post_output_dir = instance_id + "_post"
#             get_post_output(instance_id,
#                 "%s/%s" % (output_dir, post_output_dir),
#                 settings)

#             finished_nodes.append(node)
#         else:
#             print "job still running on %s: %s\
#             " % (instance_id, botocloudconnector.get_instance_ip(instance_id, settings))

#     return (error_nodes, finished_nodes)


def run_post_task(instance_id, settings):
    """
        Start the task on the instance, then hang and
        periodically check its state.
    """
    logger.info("run_post_task %s" % instance_id)
    ip = botocloudconnector.get_instance_ip(instance_id, settings)
    ssh = open_connection(ip_address=ip,
        settings=settings)

    #pids = get_package_pids(ssh, settings['COMPILE_FILE'])
    #logger.debug("pids=%s" % pids)
    #if len(pids) > 1:
     #   logger.error("warning:multiple packages running")
      #  raise PackageFailedError("multiple packages running")

    post_processing_dest = os.path.join(settings['POST_PROCESSING_DEST_PATH_PREFIX'],
        settings['POST_PAYLOAD_CLOUD_DIRNAME'])

    run_command(ssh, "cp %s %s &\
    " % (os.path.join(settings['PAYLOAD_DESTINATION'],
        settings['PAYLOAD_CLOUD_DIRNAME'],
         "hrmc01.xyz"), post_processing_dest))

    run_command(ssh, "cd %s; ./%s >& %s &\
    " % (post_processing_dest,
         settings['POST_PAYLOAD_COMPILE_FILE'], "output"))

