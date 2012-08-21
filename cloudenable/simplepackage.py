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
import paraproxy
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
	print settings.USER_NAME
	ip = _get_node_ip(instance_id)
	ssh = _open_connection(ip)
	_install_deps(ssh,settings.DEPENDS)
	_mkdir(ssh,dest_path_prefix)
	_put_file(ssh,settings.PAYLOAD, dest_path_prefix)
	_unpack(ssh,dest_path_prefix, settings.PAYLOAD)


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
		_upload_input(ssh, fname)


def run_task(instance_id):
	"""
	Start the task on the node
	"""
	print "run_task %s" % instance_id
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


def _run_command(ssh):
	stdin, stdout, stderr = ssh.exec_command("uptime")
	return stdout.readlines()

def _run_sudo_command(ssh):
	stdin, stdout, stderr = ssh.exec_command("sudo dmesg")
	stdin.write(password + '\n')
	stdin.flush()
	return stdout.readlines()


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
	ssh.connect(ip_address, username=settings.USER_NAME, password=settings.PASSWORD, timeout=60, port=80)
	return ssh


def _put_file(ssh,file,path):
	ftp = ssh.open_sftp()
	dest_file = os.path.join(path,file).replace('\\', '/'),
	ftp.put(file, dest_file)


def _install_deps(ssh,packages):
	for pack in packages:
		_run_sudo_command(ssh,'sudo yum install %s' % pack)


def _mkdir(ssh,dir):
	_run_command(ssh,"mkdir %s" % dir)


def _unpack(ssh,path,file):
	_run_sudo_command(ssh,'tar xzvf %s' % (os.path.join(path,file)))


def _upload_input(ssh,input_files):
	for input in inputfiles:
		_put_file(ssh,input,dest_path_prefix)		


def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath

