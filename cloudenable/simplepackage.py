# Deploy Generic Nectar node

import os
import paramiko
import logging
import time
import logging.config
import sys
import traceback

from libcloud.compute.types import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.providers import get_driver
import hashlib

#from libcloud.compute.base import NodeImage
#from libcloud.compute.deployment import ScriptDeployment

#http://docs.python.org/howto/logging.html#logging-basic-tutorial
logger = logging.getLogger(__name__)
NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']


class Error(Exception):
    pass


class PackageFailedError(Error):
    pass


def _create_cloud_connection(settings):
    EC2_ACCESS_KEY = settings['EC2_ACCESS_KEY']
    EC2_SECRET_KEY = settings['EC2_SECRET_KEY']

    OpenstackDriver = get_driver(Provider.EUCALYPTUS)
    logger.debug("Connecting... %s" % OpenstackDriver)
    conn = OpenstackDriver(EC2_ACCESS_KEY, secret=EC2_SECRET_KEY,
                           host="nova.rc.nectar.org.au", secure=False,
                           port=8773, path="/services/Cloud")
    logger.debug("Connected")

    return conn


def create_environ(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return id
    """
    logger.info("create_environ")
    conn = _create_cloud_connection(settings)
    images = conn.list_images()
    sizes = conn.list_sizes()

    image1 = [i for i in images if i.id == 'ami-0000000d'][0]
    size1 = [i for i in sizes if i.id == settings['VM_SIZE']][0]
    #print settings['SECURITY_GROUP
    #print image1
    #print size1
    #print settings['PRIVATE_KEY_NAME
    try:
        all_instances = []
        print(" Creating %d VM instance(s)" % number_vm_instances)
        instance_count = 0
        while instance_count < number_vm_instances:
            new_instance = conn.create_node(name="New Centos VM instance",
                size=size1, image=image1,
                ex_keyname=settings['PRIVATE_KEY_NAME'],
                ex_securitygroup=settings['SECURITY_GROUP'])
            all_instances.append(new_instance)
            instance_count += 1
    except Exception, e:
        if "QuotaError" in e[0]:
            print " Quota Limit Reached: "
            print "\t %s instances are created." % len(all_instances)
            print "\t Additional %s instances will not be created" % (number_vm_instances - len(all_instances))
        else:
            traceback.print_exc(file=sys.stdout)

    if all_instances:
        all_running_instances = _wait_for_instance_to_start_running(all_instances, settings)
        _store_md5_on_instances(all_running_instances, settings)
        print 'Created VM instances:'
        print_all_information(settings, all_running_instances)


def _store_md5_on_instances(all_instances, settings):
    group_id = _generate_group_id(all_instances)
    print " Creating group '%s'" % group_id
    for instance in all_instances:
        # login and check for md5 file

        instance_id = instance.name
        ip = _get_node_ip(instance_id, settings)
        logger.info("Registering %s (%s) to group '%s'"
                    % (instance_id, ip, group_id))
        md5_written = False
        while not md5_written:
            try:
                ssh = _open_connection(ip_address=ip,
                                       username=settings['USER_NAME'],
                                       password=settings['PASSWORD'],
                                       settings=settings)
                group_id_path = settings['GROUP_ID_DIR']+"/"+group_id
                _run_command(ssh, "mkdir %s" % settings['GROUP_ID_DIR'])
                _run_command(ssh, "touch %s" % group_id_path)
                md5_written = True
            except Exception:
                time.sleep(settings['CLOUD_SLEEP_INTERVAL'])
                logger.info("Registration in progress ...")


def _generate_group_id(all_instances):
    md5_starter_string = ""
    for instance in all_instances:
        md5_starter_string += instance.name

    md5 = hashlib.md5()
    md5.update(md5_starter_string)
    group_id = md5.hexdigest()

    return group_id


def _wait_for_instance_to_start_running(all_instances, settings):
    all_running_instances = []
    while all_instances:
        for instance in all_instances:
            instance_id = instance.name
            if is_instance_running(instance_id, settings):
                all_running_instances.append(instance)
                all_instances.remove(instance)
                logger.info('Current status of Instance %s: %s'
                % (instance_id, NODE_STATE[NodeState.RUNNING]))
            else:
                logger.info('Current status of Instance %s: %s'
                    % (instance_id, NODE_STATE[instance.state]))

        time.sleep(settings['CLOUD_SLEEP_INTERVAL'])

    return all_running_instances


def _wait_for_instance_to_terminate(all_instances, settings):
    while all_instances:
        for instance in all_instances:
            instance_id = instance.name
            if not is_instance_running(instance_id, settings):
              #  all_running_instances.append(instance)
                all_instances.remove(instance)
                logger.info('Current status of Instance %s: %s'
                % (instance_id, NODE_STATE[NodeState.TERMINATED]))
            else:
                logger.info('Current status of Instance %s: %s'
                    % (instance_id, NODE_STATE[instance.state]))

        time.sleep(settings['CLOUD_SLEEP_INTERVAL'])


def print_running_node_id(settings):
    """
        Print ID and IP of currently running nodes
    """
    conn = _create_cloud_connection(settings)
    counter = 1
    nodes = conn.list_nodes()
    if not nodes:
        logger.info("No running VM instances")

    else:
        logger.info('Currently running VM instances:')
        for i in nodes:
            logger.info('Node %d: %s %s' % (counter, i.name,
                                        _get_node_ip(i.name, settings)))
            counter += 1


def _print_available_groups(settings):
    conn = _create_cloud_connection(settings)
    all_instances = conn.list_nodes()
    all_groups = []
    for instance in all_instances:
        instance_id = instance.name
        ip = _get_node_ip(instance_id, settings)
        ssh = _open_connection(ip_address=ip,
                                       username=settings['USER_NAME'],
                                       password=settings['PASSWORD'],
                                       settings=settings)
        res = _run_command(ssh, "ls %s " % settings['GROUP_ID_DIR'])
        if len(res) > 0 and not res[0] in all_groups:
            all_groups.append(res[0])

    if not all_groups:
        logger.info("No available groups")
        sys.exit(1)
    else:
        logger.info("Available groups:")
        counter = 1
        for group in all_groups:
            logger.info("Group %d: %s" % (counter,group))
            counter += 1


def print_all_information(settings, all_instances):
    """
        Print information about running instances
            - ID
            - IP
            - VM type
            - list of groups
    """
    if not all_instances:
        print '\t No running instances'
        sys.exit(1)

    counter = 1
    print '\tNo.\tID\t\tIP\t\tPackage\t\tGroup'
    for instance in all_instances:
        instance_id = instance.name
        ip = _get_node_ip(instance_id, settings)
        ssh = _open_connection(ip_address=ip,
                                       username=settings['USER_NAME'],
                                       password=settings['PASSWORD'],
                                       settings=settings)
        group_name = _run_command(ssh, "ls %s " % settings['GROUP_ID_DIR'])
        vm_type = 'Other'
        res = _run_command(ssh, "[ -d %s ] && echo exists" % settings['GROUP_ID_DIR'])
        if 'exists\n' in res:
            vm_type = 'RMIT'

        if not group_name:
            group_name = '-'

        print '\t%d:\t%s\t%s\t%s\t\t%s' % (counter, instance_id,
                                        ip, vm_type, group_name)
        counter += 1


def is_instance_running(instance_id, settings):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance_running = False
    conn = _create_cloud_connection(settings)
    nodes = conn.list_nodes()
    for i in nodes:
        if i.name == instance_id and i.state == NodeState.RUNNING:
            instance_running = True
            break
    return instance_running


def _get_node(instance_id, settings):
    """
        Get a reference to node with instance_id
    """
    conn = _create_cloud_connection(settings)
    nodes = conn.list_nodes()
    this_node = []
    for i in nodes:
        if i.name == instance_id:
            this_node = i
            break

    return this_node


def _get_node_ip(instance_id, settings):
    """
        Get the ip address of a node
    """
    #TODO: throw exception if can't find instance_id
    conn = _create_cloud_connection(settings)
    ip = ''
    while instance_id == '' or ip == '':
        nodes = conn.list_nodes()
        for i in nodes:
            if i.name == instance_id and len(i.public_ips) > 0:
                ip = i.public_ips[0]
                break
    return ip


def collect_instances(settings, group_id=None, instance_id=None, all_VM=False):
    conn = _create_cloud_connection(settings)
    all_instances = []
    if all_VM:
        all_instances = conn.list_nodes()
    elif group_id:
        all_instances = _get_rego_nodes(group_id, settings)
    elif instance_id:
        if is_instance_running(instance_id, settings):
            all_instances.append(_get_node(instance_id, settings))

    return all_instances


def confirm_teardown(settings, all_instances):
    print "Instances to be deleted are "
    print_all_information(settings, all_instances)

    teardown_confirmation = None
    while not teardown_confirmation:
        teardown_confirmation = raw_input(
                                "Are you sure you want to delete (yes/no)? ")
        if teardown_confirmation != 'yes' and teardown_confirmation != 'no':
            teardown_confirmation = None

    if teardown_confirmation == 'yes':
        return True
    else:
        return False


def destroy_environ(settings, all_instances):
    """
        Terminate
            - all instances, or
            - a group of instances, or
            - a single instance
    """
    logger.info("destroy_environ")
    if not all_instances:
        logging.error("No running instance(s)")
        sys.exit(1)

    logger.info("Terminating %d VM instance(s)" %len(all_instances))
    conn = _create_cloud_connection(settings)
    for instance in all_instances:
        try:
            conn.destroy_node(instance)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    _wait_for_instance_to_terminate(all_instances, settings)


def setup_task(instance_id, settings):
    """
    Transfer the task package to the node and install
    """

    logger.info("setup_task %s " % instance_id)

    ip = _get_node_ip(instance_id, settings)
    ssh = _open_connection(ip_address=ip, username=settings['USER_NAME'],
                           password=settings['PASSWORD'], settings=settings)
    res = _install_deps(ssh, packages=settings['DEPENDS'],
                        settings=settings, instance_id=instance_id)
    logger.debug("install res=%s" % res)
    res = _mkdir(ssh, dir=settings['DEST_PATH_PREFIX'])
    logger.debug("mkdir res=%s" % res)
    _put_file(ssh, source_path=settings['PAYLOAD_LOCAL_DIRNAME'],
              package_file=settings['PAYLOAD'],
              environ_dir=settings['DEST_PATH_PREFIX'])
    _unpack(ssh, environ_dir=settings['DEST_PATH_PREFIX'],
            package_file=settings['PAYLOAD'])
    _compile(ssh, environ_dir=settings['DEST_PATH_PREFIX'],
             compile_file=settings['COMPILE_FILE'],
             package_dirname=settings['PAYLOAD_CLOUD_DIRNAME'],
             compiler_command=settings['COMPILER'])


def prepare_input(instance_id, input_dir, settings,seed):
    """
        Take the input_dir and move all the contained files to the
        instance and ready

    """

    logger.info("prepare_input %s %s" % (instance_id, input_dir))
    ip = _get_node_ip(instance_id, settings)
    ssh = _open_connection(ip_address=ip, username=settings['USER_NAME'],
                           password=settings['PASSWORD'], settings=settings)
    input_dir = _normalize_dirpath(input_dir)
    dirList = os.listdir(input_dir)
    for fname in dirList:
        logger.debug(fname)
        _upload_input(ssh, input_dir, fname,
                      os.path.join(settings['DEST_PATH_PREFIX'],
                                   settings['PAYLOAD_CLOUD_DIRNAME']))
    _run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    _run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))
    _run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                (os.path.join(settings['DEST_PATH_PREFIX'],
                              settings['PAYLOAD_CLOUD_DIRNAME'])))


def run_task(instance_id, settings):
    """
        Start the task on the instance, then hang and
        periodically check its state.
    """
    logger.info("run_task %s" % instance_id)
    ip = _get_node_ip(instance_id, settings)
    ssh = _open_connection(ip_address=ip,
                           username=settings['USER_NAME'],
                           password=settings['PASSWORD'], settings=settings)
    if len(_get_package_pid(ssh, settings['COMPILE_FILE'])) > 1:
        logger.error("warning:multiple packages running")
        raise PackageFailedError("multiple packages running")
    _run_command(ssh, "cd %s; ./%s >& %s &"
                 % (os.path.join(
                    settings['DEST_PATH_PREFIX'],
                    settings['PAYLOAD_CLOUD_DIRNAME']),
                    settings['COMPILE_FILE'], "output"))
    import time
    attempts = settings['RETRY_ATTEMPTS']
    for x in range(0, attempts):
        time.sleep(5)  # to give process enough time to start
        pid = _get_package_pid(ssh, settings['COMPILE_FILE'])
        logger.debug(pid)
        if pid:
            break
    else:
        raise PackageFailedError("package did not start")
    return pid.split(' ')
    pass


def get_output(instance_id, output_dir, settings):
    """
        Retrieve the output from the task on the node
    """
    logger.info("get_output %s" % instance_id)
    ip = _get_node_ip(instance_id, settings)
    ssh = _open_connection(ip_address=ip,
                           username=settings['USER_NAME'],
                           password=settings['PASSWORD'], settings=settings)
    try:
        os.mkdir(output_dir)
    except OSError, e:
        logger.debug("output directory %s already exists: %s" % (output_dir,e))
        #sys.exit(1)
    logger.info("output directory is %s" % output_dir)
    for file in settings['OUTPUT_FILES']:
        _get_file(ssh, os.path.join(settings['DEST_PATH_PREFIX'],
                                    settings['PAYLOAD_CLOUD_DIRNAME']),
                  file, output_dir)
    # TODO: do integrity check on output files
    pass


def job_finished(instance_id, settings):
    """
        Return True if package job on instance_id has job_finished
    """

    ip = _get_node_ip(instance_id, settings)
    ssh = _open_connection(ip_address=ip,
                           username=settings['USER_NAME'],
                           password=settings['PASSWORD'], settings=settings)
    pid = _get_package_pid(ssh, settings['COMPILE_FILE'])
    return not pid


def _open_connection(ip_address, username, password, settings):
    # open up the connection
    ssh = paramiko.SSHClient()
    # autoaccess new keys

    ssh.load_system_host_keys(os.path.expanduser(os.path.join("~",
                                                              ".ssh",
                                                              "known_hosts")))
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    #TODO: handle exceptions if connection does not work.
    # use private key if exists
    if os.path.exists(settings['PRIVATE_KEY']):
        privatekeyfile = os.path.expanduser(settings['PRIVATE_KEY'])
        mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        ssh.connect(ip_address, username=username, timeout=60, pkey=mykey)
    else:
        logger.debug("%s %s %s" % (ip_address, username, password))
        logger.debug(ssh)
        ssh.connect(ip_address, username=username,
                    password=password, timeout=60)

    #channel = ssh.invoke_shell().open_session()

    return ssh


def _run_command(ssh, command, current_dir=None):
    logger.debug("%s %s " % (current_dir, command))
    if current_dir:
        command = "cd %s;%s" % (current_dir, command)
    logger.debug(command)
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.readlines()


def _get_channel_data(chan):
    tCheck = 0
    res = ''
    # we don't know when data is exhausted.
    for i in range(0, 10):
        logger.debug("about to check for ready for data %s" % i)
        timeout = False
        # this is the key waiting loop for the next bit of data
        while not chan.recv_ready():
            time.sleep(5)
            tCheck += 1
            if tCheck >= 10:
                logger.error('time out for waiting for new data')
                # TODO: add exeption here
                timeout = True
                break
        if not timeout:
            logger.debug("about to get data")
            out = chan.recv(9999)
            logger.debug("got data out=%s" % out)
            res += out
            logger.debug("res data = %s" % res)
        else:
            logger.debug("timeout triggered so no data avail now")
    logger.debug("final res data = %s" % res)
    return out


def _install_deps(ssh, packages, settings, instance_id):
    for pack in packages:
        stdout, stderr = _run_sudo_command(
            ssh, 'yum -y install %s' % pack,
            settings=settings, instance_id=instance_id)
        logger.debug("install stdout=%s" % stdout)
        logger.debug("install stderr=%s" % stderr)


def _run_sudo_command(ssh, command, settings, instance_id):

    chan = ssh.invoke_shell()
    chan.send('sudo -s\n')
    full_buff = ''
    buff = ''
    while not '[%s@%s ~]$ ' % (settings['USER_NAME'], instance_id) in buff:
        resp = chan.recv(9999)
        #logger.debug("resp=%s" % resp)
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    buff = ''
    while not '[root@%s %s]# ' % (instance_id, settings['USER_NAME']) in buff:
        resp = chan.recv(9999)
        #logger.debug("resp=%s" % resp)
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''
    while not '[%s@%s ~]$ ' % (settings['USER_NAME'], instance_id) in buff:
        resp = chan.recv(9999)
        #logger.debug("resp=%s" % resp)
        buff += resp
    logger.debug("3buff = %s" % buff)
    full_buff += buff

    chan.close()
    return (full_buff, '')


def _unpack(ssh, environ_dir, package_file):
    res = _run_command(
        ssh, 'tar --directory=%s --extract --gunzip --verbose --file=%s'
        % (environ_dir, os.path.join(environ_dir, package_file)))
    logger.debug(res)


def _compile(ssh, environ_dir, compile_file, package_dirname,
             compiler_command):
    _run_command(ssh, "%s %s.f -o %s " % (compiler_command,
                                          compile_file,
                                          compile_file),
                 current_dir=os.path.join(environ_dir, package_dirname))


def _upload_input(ssh, source_path_prefix, input_file, dest_path_prefix):
        _put_file(ssh, source_path_prefix, input_file, dest_path_prefix)


def _mkdir(ssh, dir):
    _run_command(ssh, "mkdir %s" % dir)


def _get_file(ssh, source_path, package_file, environ_dir):
    ftp = ssh.open_sftp()
    logger.debug("%s %s %s" % (source_path, package_file, environ_dir))
    source_file = os.path.join(source_path, package_file).replace('\\', '/')
    dest_file = os.path.join(environ_dir, package_file).replace('\\', '/')
    logger.debug("%s %s" % (source_file, dest_file))
    try:
        ftp.get(source_file, dest_file)
    except IOError:
        logger.warning("%s not found" % package_file)


def _put_file(ssh, source_path, package_file, environ_dir):
    ftp = ssh.open_sftp()
    logger.debug("%s %s" % (source_path, environ_dir))
    source_file = os.path.join(source_path, package_file).replace('\\', '/')
    dest_file = os.path.join(environ_dir, package_file).replace('\\', '/')
    logger.debug("%s %s" % (source_file, dest_file))
    ftp.put(source_file, dest_file)


def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath


def _get_package_pid(ssh, command):
    pid = _run_command(ssh, "/sbin/pidof %s" % command)
    if len(pid):
        pid = pid[0]  # if some returns, the pids are in first element
    return pid


def _get_rego_nodes(group_id, settings):
    """
    Returns nectar nodes that are currently packaged enabled.
    """
    # get all available nodes
    conn = _create_cloud_connection(settings)
    packaged_node = []
    for node in conn.list_nodes():
        # login and check for md5 file
        ssh = _open_connection(ip_address=_get_node_ip(node.name, settings),
                               username=settings['USER_NAME'],
                               password=settings['PASSWORD'], settings=settings)
        # NOTE: assumes use of bash shell
        group_id_path = settings['GROUP_ID_DIR']+"/"+group_id
        res = _run_command(ssh, "[ -f %s ] && echo exists" % group_id_path)
        logger.debug("res=%s" % res)
        if 'exists\n' in res:
            logger.debug("node %s exists for group %s "
                         % (node.name, group_id))
            packaged_node.append(node)
        else:
            logger.debug("NO node for %s exists for group %s "
                         % (node.name, group_id))
    return packaged_node


def _status_of_nodeset(nodes, output_dir, settings):
    """
    Return lists that describe which of the set of nodes are finished or
    have disappeared
    """
    error_nodes = []
    finished_nodes = []

    for node in nodes:
        instance_id = node.name
        if not is_instance_running(instance_id, settings):
            # An unlikely situation where the node crashed after is was
            # detected as registered.
            logging.error('Instance %s not running' % instance_id)
            error_nodes.append(node)
            continue
        if job_finished(instance_id, settings):
            print "done. output is available"
            get_output(instance_id,
                       "%s/%s" % (output_dir, node.name),
                       settings)
            finished_nodes.append(node)
        else:
            print "job still running on %s: %s" % (instance_id,
                                                   _get_node_ip(instance_id,
                                                                settings))

    return (error_nodes, finished_nodes)


def setup_multi_task(group_id, settings):
    """
    Transfer the task package to the instances in group_id and install
    """
    logger.info("setup_multi_task %s " % group_id)
    packaged_nodes = _get_rego_nodes(group_id, settings)
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
        t = threading.Thread(target=setup_worker, args=(node.name,))
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
    nodes = _get_rego_nodes(group_id, settings)
    error_nodes, finished_nodes = _status_of_nodeset(nodes, output_dir, settings)

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
    nodes = _get_rego_nodes(group_id, settings)

    pids = []
    for node in nodes:
        try:
            pid = run_task(node.name, settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start package on node %s" % node)
            #TODO: cleanup node of copied input files etc.
        else:
            pids.append(pid)

    pids = dict(zip(nodes, pids))
    return pids


def prepare_multi_input(group_id, input_dir, settings, seed):
    """
        Take the input_dir and move all the contained files to the
        instances in the group and ready

    """

    nodes = _get_rego_nodes(group_id, settings)



    import random
    random.seed(seed)
    seeds = {}
    for node in nodes:
        # FIXME: is the random supposed to be positive or negative?
        seeds[node] = random.randrange(0,settings['MAX_SEED_INT'])

    if seed:
        print ("seed for full package run = %s" % seed)
    else:
        print ("seeds for each node in group %s = %s" % (group_id,[(x.name,seeds[x]) for x in seeds.keys()]))


    logger.debug("seeds = %s" % seeds)
    for node in nodes:
        instance_id = node.name
        logger.info("prepare_input %s %s" % (instance_id, input_dir))
        ip = _get_node_ip(instance_id, settings)
        ssh = _open_connection(ip_address=ip, username=settings['USER_NAME'],
                               password=settings['PASSWORD'], settings=settings)
        input_dir = _normalize_dirpath(input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:
            logger.debug(fname)
            _upload_input(ssh, input_dir, fname,
                          os.path.join(settings['DEST_PATH_PREFIX'],
                                       settings['PAYLOAD_CLOUD_DIRNAME']))
        _run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        _run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))
        _run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME'])))

        _run_command(ssh, "cd %s; sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' rmcen.inp" %
                    (os.path.join(settings['DEST_PATH_PREFIX'],
                                  settings['PAYLOAD_CLOUD_DIRNAME']), seeds[node]))



