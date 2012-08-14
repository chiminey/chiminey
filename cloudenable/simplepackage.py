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



def create_environ():
	"""
	Create the Nectar Node and return id
	"""
	print "create_environ"
	return 42

def setup_task(instance_id):
	"""
	Transfer the task package to the node and install
	"""
	print "setup_task %s " % instance_id
	pass 

def prepare_input(instance_id, input_dir):
	"""
	Take the input_dir and move to node and ready
	"""
	print "prepare_input %d %s" % (instance_id, input_dir)
	pass

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

import paramiko

def _test_paramiko():
	""" 
	Tests that we can connect to a server and issue various commands
		See http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/
	"""

	# You will need to change these
	ip_address = "127.0.0.1"
	user_name = "ianthomas"
	password = "EICXJcQ5"

	# open up the connection
	ssh = paramiko.SSHClient()
	# autoaccess new keys
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(ip_address, username=user_name, password=password)

	# run a user command
	stdin, stdout, stderr = ssh.exec_command("uptime")
	print stdout.readlines()

	# run a command that requires input redirection
	stdin, stdout, stderr = ssh.exec_command("sudo dmesg")
	# assumes user can use sudo
	stdin.write(password + '\n')
	stdin.flush()
	print stdout.readlines()

	# get and put files
	ftp = ssh.open_sftp()
	#ftp.get('remotefile.py', 'localfile.py')
	#ftp.put('localfile.py','remotefile.py')

	# put whole directory
	#put_dir_recursively(ssh, localpath, remotepath, preserve_perm=True)

	ssh.close()


def _normalize_dirpath(dirpath):
    while dirpath.endswith("/"):
        dirpath = dirpath[:-1]
    return dirpath


def _mkdir(sftp, remotepath, mode=0777, intermediate=False):
    remotepath = .normalize_dirpath(remotepath)
    if intermediate:
        try:
            sftp.mkdir(remotepath, mode=mode)
        except IOError, e:
            mkdir(sftp, remotepath.rsplit("/", 1)[0], mode=mode,
                       intermediate=True)
            return sftp.mkdir(remotepath, mode=mode)
    else:
        sftp.mkdir(remotepath, mode=mode)


def _put_dir_recursively(ssh,localpath, remotepath, preserve_perm=True):
    """
    	Upload local directory to remote recursively 
    	from http://stackoverflow.com/questions/4409502/directory-transfers-on-paramiko
    """

    assert remotepath.startswith("/"), "%s must be absolute path" % remotepath

    # normalize
    localpath =  _normalize_dirpath(localpath)
    remotepath = _normalize_dirpath(remotepath)

    sftp = ssh.open_sftp()

    try:
        sftp.chdir(remotepath)
        localsuffix = localpath.rsplit("/", 1)[1]
        remotesuffix = remotepath.rsplit("/", 1)[1]
        if localsuffix != remotesuffix:
            remotepath = os.path.join(remotepath, localsuffix)
    except IOError, e:
        pass

    for root, dirs, fls in os.walk(localpath):
        prefix = os.path.commonprefix([localpath, root])
        suffix = root.split(prefix, 1)[1]
        if suffix.startswith("/"):
            suffix = suffix[1:]

        remroot = os.path.join(remotepath, suffix)

        try:
            sftp.chdir(remroot)
        except IOError, e:
            if preserve_perm:
                mode = os.stat(root).st_mode & 0777
            else:
                mode = 0777
            self._mkdir(sftp, remroot, mode=mode, intermediate=True)
            sftp.chdir(remroot)

        for f in fls:
            remfile = os.path.join(remroot, f)
            localfile = os.path.join(root, f)
            sftp.put(localfile, remfile)
            if preserve_perm:
                sftp.chmod(remfile, os.stat(localfile).st_mode & 0777)


if __name__ == '__main__':
	_test_paramiko()
