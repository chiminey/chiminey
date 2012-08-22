# Deploy Generic Nectar node

# Install required dependencies (e.g., Fortran on VM)
# Transfer program source or binary to node and install
# Get input data from command line or from input files or directories
# Transfer any input files/directores to node using SFTP/SCP
# Run the program on the node.
# Retrieve the data from the node back to the client
# Terminate the instance.
# We might want to organise a node to be run multiple times with different parameters, rather than deploying
# and destroying each time.  This could be an extension if we get time.

import os
import paramiko
import settings



def create_environ():
	"""
	Create the Nectar Node and return id
	"""
	print "create_environ"
	setup_task(42)
	return 42


def setup_task(instance_id):
	"""
	Transfer the task package to the node and install
	"""
	print "setup_task %s " % instance_id
	ip = _get_node_ip(instance_id)
	ssh = _open_connection(ip)
	_install_deps(ssh, packages=settings.DEPENDS)
	_mkdir(ssh, dir=settings.DEST_PATH_PREFIX)
	_put_file(ssh, source_path="payload", package_file=settings.PAYLOAD, environ_dir=settings.DEST_PATH_PREFIX)
	_unpack(ssh, environ_dir=settings.DEST_PATH_PREFIX, package_file=settings.PAYLOAD)
	_compile(ssh, environ_dir=settings.DEST_PATH_PREFIX, 
		compile_file=settings.COMPILE_FILE, 
		package_dirname=settings.PAYLOAD_DIRNAME)


def prepare_input(instance_id, input_dir):
	"""
	Take the input_dir and move all the contained files to the node and ready
	"""
	print "prepare_input %d %s" % (instance_id, input_dir)
	ip = _get_node_ip(instance_id)
	ssh = _open_connection(ip)
	input_dir = _normalize_dirpath(input_dir)
	dirList=os.listdir(input_dir)
	for fname in dirList:
		print fname
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
	Start the task on the node
	"""
	print "run_task %s" % instance_id 
	ip = _get_node_ip(instance_id) 
	ssh = _open_connection(ip)
	_run_command(ssh, "cd %s; ./a.out >& output &" % (os.path.join(settings.DEST_PATH_PREFIX, settings.PAYLOAD_DIRNAME)))

	pass


def get_output(instance_id):
	""" 
	Retrieve the output from the task on the node
	"""
	print "get_output %s" % instance_id
	pass

def destroy_environ(instance_id):
	""" 
	terminate the instance 
	"""
	print "destroy_environ %s" % instance_id
	pass


def _get_node_ip(instance_id):
	"""
		Get the ip adress of a node
	"""
	# TODO: use libcloud to return the external ip address of the node
	return '115.146.94.148'


def _open_connection(ip_address):
	# open up the connection
	ssh = paramiko.SSHClient()
	paramiko.util.log_to_file("out")
	# autoaccess new keys
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

	# TODO: use PKI
	print "%s %s %s" % (ip_address, settings.USER_NAME, settings.PASSWORD)
	print ssh
	ssh.connect(ip_address, username=settings.USER_NAME, password=settings.PASSWORD, timeout=60)
	return ssh


def _run_command(ssh, command,current_dir=None):
	print current_dir, command
	if current_dir:
		command = "cd %s;%s" % (current_dir,command)
	print command
	stdin, stdout, stderr = ssh.exec_command(command)
	return stdout.readlines()

def _run_sudo_command(ssh,command,password=None):
	stdin, stdout, stderr = ssh.exec_command(command,password)
	stdin.write(password + '\n')
	stdin.flush()
	return stdout.readlines()


def _put_file(ssh, source_path, package_file, environ_dir):
	ftp = ssh.open_sftp()
	print source_path, environ_dir
	source_file = os.path.join(source_path,package_file).replace('\\','/')
	dest_file = os.path.join(environ_dir,package_file).replace('\\', '/')
	print source_file, dest_file
 	ftp.put(source_file, dest_file)


def _unpack(ssh,environ_dir,package_file):
	print _run_command(ssh,'tar --directory=%s --extract --gunzip --verbose --file=%s' 
		% (environ_dir, os.path.join(environ_dir, package_file)))


def _compile(ssh, environ_dir,compile_file, package_dirname):
	_run_command(ssh, "%s %s" % (settings.COMPILER, compile_file),
		current_dir=os.path.join(environ_dir, package_dirname))

def _install_deps(ssh,packages):
	for pack in packages:
	    _run_sudo_command(ssh,'sudo yum install %s' % pack,settings.PASSWORD)


def _upload_input(ssh,source_path_prefix,input_file,dest_path_prefix):
		_put_file(ssh, source_path_prefix, input_file,dest_path_prefix)		

def _mkdir(ssh,dir):
	_run_command(ssh,"mkdir %s" % dir)


def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath

