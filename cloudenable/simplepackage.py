# Deploy Generic Nectar node

import os
import paramiko
import settings
import logging
import time
import logging.config
import sys
import traceback

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from libcloud.compute.base import NodeImage
from libcloud.compute.deployment import ScriptDeployment


#http://docs.python.org/howto/logging.html#logging-basic-tutorial
logger = logging.getLogger(__name__)


class Error(Exception):
	pass
 
class PackageFailedError(Error):
	pass
 
def _create_connection():
    EC2_ACCESS_KEY=settings.EC2_ACCESS_KEY
    EC2_SECRET_KEY=settings.EC2_SECRET_KEY
    
    OpenstackDriver = get_driver(Provider.EUCALYPTUS)
    #print("Connecting...",OpenstackDriver)
    conn = OpenstackDriver(EC2_ACCESS_KEY, secret=EC2_SECRET_KEY, host="nova.rc.nectar.org.au", secure=False, port=8773, path="/services/Cloud")
    #print ("Connected")
    
    return conn

def create_environ():
    """
        Create the Nectar Node and return id
    """
    logger.info("create_environ")
    conn = _create_connection()
    images = conn.list_images()
    sizes = conn.list_sizes()
            
    image1 = [i for i in images if i.id == 'ami-0000000d'][0]
    size1 = [i for i in sizes if i.id == 'm1.small'][0]
     
    instance_id = ''
    try:
        new_instance = conn.create_node(name="New Centos Node",size=size1,image=image1, ex_keyname=settings.PRIVATE_KEY_NAME, ex_securitygroup=settings.SECURITY_GROUP)

        instance_id = new_instance.name
        print 'Instance CREATED: ID=%s' %instance_id
    
    except Exception:
        traceback.print_exc(file=sys.stdout)
        _print_running_node_id(conn)
        
	    
    return instance_id


def _print_running_node_id(conn):
    counter = 1
    nodes = conn.list_nodes()
    print ('ID and IP for currently running node instances')
    for i in nodes:
        print 'Node', counter, i.name, _get_node_ip(i.name)
        counter = counter+1

def is_instance_running(instance_id):
	instance_running = False
	conn = _create_connection()
	nodes = conn.list_nodes()
	for i in nodes:
		if i.name == instance_id:
			instance_running = True
			break
	return instance_running		



def _get_node(instance_id):
    """
        Get a reference to node with instance_id
    """
    conn = _create_connection()
    nodes = conn.list_nodes()
    this_node = []
    for i in nodes:
        if i.name == instance_id:   
            this_node = i
            break

    return this_node

def _get_node_ip(instance_id):
    """
        Get the ip address of a node
    """
    conn = _create_connection()
    ip = ''
    while instance_id == '' or ip == '':
        nodes = conn.list_nodes()
        for i in nodes:
            if i.name == instance_id and len(i.public_ips) > 0:   
                ip = i.public_ips[0]
                break
        
    return ip


def destroy_environ(instance_id):
    """
		Terminate the instance 
    """

    logger.info( "destroy_environ %s" % instance_id)
    this_node = _get_node(instance_id)
    conn = _create_connection()
    try:
        print conn.destroy_node(this_node)
        print 'Instance',instance_id,'DESTROYED'
            
    except Exception:
        print 'Instance',instance_id,'NOT DESTROYED'


def setup_task(instance_id):
    """
	Transfer the task package to the node and install
    """

    logger.info("setup_task %s " % instance_id)
    ip = _get_node_ip(instance_id)
    ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
    res = _install_deps(ssh, packages=settings.DEPENDS,sudo_password=settings.PASSWORD)
    logger.debug("install res=%s" % res)
    res = _mkdir(ssh, dir=settings.DEST_PATH_PREFIX)
    logger.debug("mkdir res=%s" % res)
    _put_file(ssh, source_path="payload", package_file=settings.PAYLOAD, environ_dir=settings.DEST_PATH_PREFIX)
    _unpack(ssh, environ_dir=settings.DEST_PATH_PREFIX, package_file=settings.PAYLOAD)
    _compile(ssh, environ_dir=settings.DEST_PATH_PREFIX, 
	compile_file=settings.COMPILE_FILE, 
	package_dirname=settings.PAYLOAD_DIRNAME,
	compiler_command=settings.COMPILER)


def prepare_input(instance_id, input_dir):
	"""
		Take the input_dir and move all the contained files to the instance and ready

	"""

	logger.info("prepare_input %s %s" % (instance_id, input_dir))
	ip = _get_node_ip(instance_id)
	ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
	input_dir = _normalize_dirpath(input_dir)
	dirList=os.listdir(input_dir)
	for fname in dirList:
		logger.debug(fname)
		_upload_input(ssh, input_dir, fname,
			os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME))
	_run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" % 
		(os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME)))
	_run_command(ssh, "cd %s; dos2unix rmcen.inp" % 
		(os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME)))
	_run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" % 
		(os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME)))


def run_task(instance_id):
	"""
		Start the task on the instance, then hang and periodically check its state.
	"""
	logger.info("run_task %s" % instance_id )
	ip = _get_node_ip(instance_id) 
	ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
	if len(_get_package_pid(ssh,settings.COMPILE_FILE)) > 1:
		logger.error("warning:multiple packages running")
		raise PackageFailedError("multiple packages running")
	_run_command(ssh, "cd %s; ./%s >& %s &" % (os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME),
		settings.COMPILE_FILE, "output"))
	import time
	attempts = settings.RETRY_ATTEMPTS
	for x in range(0, attempts):
		time.sleep(5) # to give process enough time to start
		pid = _get_package_pid(ssh,settings.COMPILE_FILE)
		logger.debug(pid)
		if pid:
			break
	else:
		raise PackageFailedError("package did not start") 
	return pid.split(' ')
	pass


def get_output(instance_id,output_dir):
	""" 
		Retrieve the output from the task on the node
	"""
	logger.info("get_output %s" % instance_id)
	ip = _get_node_ip(instance_id) 
	ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
	try:
		os.mkdir(output_dir)
	except exception.OSError:
		logger.warning("output directory already exists")
		sys.exit(1)	
	logger.info("output directory is %s" % output_dir)	
	for file in settings.OUTPUT_FILES:
		_get_file(ssh, os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME), file, output_dir)
	# TODO: do integrity check on output files
	pass


def job_finished(instance_id):
	""" 
		Return True if package job on instance_id has job_finished
	"""
	ip = _get_node_ip(instance_id) 
	ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
	pid = _get_package_pid(ssh,settings.COMPILE_FILE) 
	return not pid


def _open_connection(ip_address, username, password):
	# open up the connection
	ssh = paramiko.SSHClient()
	# autoaccess new keys
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))


	# use private key if exists
	if os.path.exists(settings.PRIVATE_KEY):
		privatekeyfile = os.path.expanduser(settings.PRIVATE_KEY)
		mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
		ssh.connect(ip_address, username=username, timeout=60, pkey = mykey)
	else:
		logger.debug("%s %s %s" % (ip_address, username, password))
		logger.debug(ssh)
		ssh.connect(ip_address, username=username, password=password,timeout=60)

	#channel = ssh.invoke_shell().open_session()

	return ssh


def _run_command(ssh, command,current_dir=None):
 	logger.info("%s %s " % (current_dir, command))
	if current_dir:
		command = "cd %s;%s" % (current_dir,command)
	logger.info(command)
	stdin, stdout, stderr = ssh.exec_command(command)
	return stdout.readlines()

def _get_channel_data(chan):
	tCheck = 0
	while not chan.recv_ready():
 		time.sleep(10)
        tCheck+=1
        if tCheck >= 6:
            print 'time out'#TODO: add exeption here              
	out =  chan.recv(9999) 
	return out

def _run_sudo_command(ssh,command,password=None):

	# transport = paramiko.Transport((host, port))            
 #    transport.connect(username = username, password = password)
 #    chan = paramiko.transport.open_session()
 #    chan.setblocking(0)
 #    chan.invoke_shell()
 
 #    out = ''
 
 #    chan.send(cmd+'\n')
 
 #    tCheck = 0
 
 #    # Wait for it.....
 #    while not chan.recv_ready():
 #        time.sleep(10)
 #        tCheck+=1
 #        if tCheck >= 6:
 #            print 'time out'#TODO: add exeption here 
 #            return False
 #    stdout = chan.recv(1024)
	 
	logger.debug(command)
	t = ssh.get_transport() 
	chan = t.open_session() 
	chan.get_pty()
	chan.exec_command('sudo -s') 
	time.sleep(5)

	res = _get_channel_data(chan)
	logger.debug("res=%s" % res)

	chan.send(password + '\n') 
	time.sleep(5)

	res = _get_channel_data(chan)
	logger.debug("res=%s" % res)

	chan.send('%s\n' % command) 
	time.sleep(25)

	res = _get_channel_data(chan)
	logger.debug("res=%s" % res)

	
	
	# tCheck = 0
	# while not chan.recv_stderr_ready():
 #  		time.sleep(10)
 #        tCheck+=1
 #        if tCheck >= 6:
 #            print 'time out'#TODO: add exeption here              
	#out =  chan.recv_stderr(9999) 
	#logger.debug("err = %s" % err)

	# TODO: handle stderr
	chan.send('exit\n') 

	return (res, '')


def _unpack(ssh,environ_dir,package_file):
	res = _run_command(ssh,'tar --directory=%s --extract --gunzip --verbose --file=%s' 
		% (environ_dir, os.path.join(environ_dir, package_file)))
	logger.debug(res)


def _compile(ssh, environ_dir,compile_file, package_dirname,compiler_command):
	_run_command(ssh, "%s %s.f -o %s " % (compiler_command, compile_file, compile_file),
		current_dir=os.path.join(environ_dir, package_dirname))


def _install_deps(ssh,packages,sudo_password):
	for pack in packages:
		stdout, stderr = _run_sudo_command(ssh,'sudo yum -y install %s' % pack,password=sudo_password)
		logger.debug("install stdout=%s" % stdout)
		logger.debug("install stderr=%s" % stderr)


def _upload_input(ssh,source_path_prefix,input_file,dest_path_prefix):
		_put_file(ssh, source_path_prefix, input_file,dest_path_prefix)		


def _mkdir(ssh,dir):
	_run_command(ssh,"mkdir %s" % dir)


def _get_file(ssh, source_path, package_file, environ_dir):
	ftp = ssh.open_sftp()
	logger.debug("%s %s %s" % (source_path, package_file, environ_dir))
	source_file = os.path.join(source_path,package_file).replace('\\','/')
	dest_file = os.path.join(environ_dir,package_file).replace('\\', '/')
	logger.debug("%s %s" % (source_file, dest_file))
	try:
		ftp.get(source_file, dest_file)
	except IOError, e:
		logger.warning("%s not found" % package_file) 	


def _put_file(ssh, source_path, package_file, environ_dir):
	ftp = ssh.open_sftp()
	logger.debug("%s %s" % (source_path, environ_dir))
	source_file = os.path.join(source_path,package_file).replace('\\','/')
	dest_file = os.path.join(environ_dir,package_file).replace('\\', '/')
	logger.debug("%s %s" % (source_file, dest_file))
 	ftp.put(source_file, dest_file)


def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath


def _get_package_pid(ssh,command):
	pid = _run_command(ssh,"/sbin/pidof %s" % command)
	if len(pid):
		pid = pid[0] # if some returns, the pids are in first element
	return pid


