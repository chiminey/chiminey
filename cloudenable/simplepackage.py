# Deploy Generic Nectar node

import os
import paramiko
import settings
import logging
import logging
import logging.config

#http://docs.python.org/howto/logging.html#logging-basic-tutorial
logger = logging.getLogger(__name__)


class Error(Exception):
	pass
 
class PackageFailedError(Error):
	pass
 
def create_environ():
	"""
		Create the Nectar Node and return id
	"""
	logger.info("create_environ")
	# TODO: use libcloud to create a new node and return unique id
	setup_task(42)
	return 42


def _get_node_ip(instance_id):
	"""
		Get the ip adress of a node
	"""
	# TODO: use libcloud to return the external ip address from the id
	return '115.146.94.148'


def destroy_environ(instance_id):
	""" 
		Terminate the instance 
	"""
	logger.info( "destroy_environ %s" % instance_id)
	# TODO: use libcloud to tear down the instance
	pass


def setup_task(instance_id):
	"""
		Transfer the task package to the node and install
	"""
	logger.info("setup_task %s " % instance_id)
	ip = _get_node_ip(instance_id)
	ssh = _open_connection(ip_address=ip, username=settings.USER_NAME, password=settings.PASSWORD)
	_install_deps(ssh, packages=settings.DEPENDS,sudo_password=settings.PASSWORD)
	_mkdir(ssh, dir=settings.DEST_PATH_PREFIX)
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
	logger.info("prepare_input %d %s" % (instance_id, input_dir))
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
	paramiko.util.log_to_file("out")
	# autoaccess new keys
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

	# TODO: use PKI rather than username/password
	logger.debug("%s %s %s" % (ip_address, username, password))
	logger.debug(ssh)
	ssh.connect(ip_address, username=username, password=password, timeout=60)
	return ssh


def _run_command(ssh, command,current_dir=None):
 	logger.info("%s %s " % (current_dir, command))
	if current_dir:
		command = "cd %s;%s" % (current_dir,command)
	logger.info(command)
	stdin, stdout, stderr = ssh.exec_command(command)
	return stdout.readlines()

def _run_sudo_command(ssh,command,password=None):
	stdin, stdout, stderr = ssh.exec_command(command,password)
	stdin.write(password + '\n')
	stdin.flush()
	return stdout.readlines()


def _unpack(ssh,environ_dir,package_file):
	res = _run_command(ssh,'tar --directory=%s --extract --gunzip --verbose --file=%s' 
		% (environ_dir, os.path.join(environ_dir, package_file)))
	logger.debug(res)


def _compile(ssh, environ_dir,compile_file, package_dirname,compiler_command):
	_run_command(ssh, "%s %s.f -o %s " % (compiler_command, compile_file, compile_file),
		current_dir=os.path.join(environ_dir, package_dirname))


def _install_deps(ssh,packages,sudo_password):
	for pack in packages:
	    _run_sudo_command(ssh,'sudo yum install %s' % pack,sudo_password)


def _upload_input(ssh,source_path_prefix,input_file,dest_path_prefix):
		_put_file(ssh, source_path_prefix, input_file,dest_path_prefix)		


def _mkdir(ssh,dir):
	_run_command(ssh,"mkdir %s" % dir)


def _get_file(ssh, source_path, package_file, environ_dir):
	ftp = ssh.open_sftp()
	logger.debug(source_path, package_file, environ_dir)
	source_file = os.path.join(source_path,package_file).replace('\\','/')
	dest_file = os.path.join(environ_dir,package_file).replace('\\', '/')
	logger.debug(source_file, dest_file)
 	ftp.get(source_file, dest_file)


def _put_file(ssh, source_path, package_file, environ_dir):
	ftp = ssh.open_sftp()
	logger.debug(source_path, environ_dir)
	source_file = os.path.join(source_path,package_file).replace('\\','/')
	dest_file = os.path.join(environ_dir,package_file).replace('\\', '/')
	logger.debug(source_file, dest_file)
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


