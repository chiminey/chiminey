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
	""" terminate the instance """
	print "destroy_environ %s" % instance_id
	pass


