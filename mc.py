from cloudenable.simplepackage import *
from optparse import OptionParser

if __name__ == '__main__':


	# There are three main paths at the moment.
	# 1) Create a instance with task package installed
    # 2) Setup input, run task and retrieve output
    # 3) Destroy the instance.
    # This is because we may want to run the sequence 1,2,2,2,3

    # get command line options
	parser = OptionParser()
	parser.add_option("-n", "--nodeid", type="int", dest="instance_id",
	                  help="The instance id from the cloud infrastructure")
	parser.add_option("-i", "--inputdir", dest="input_dir",
	                  help="The local directory holding input files for the task")	
	(options, args) = parser.parse_args()

	if 'setup' in args:
		print create_environ()		
	elif 'run' in args:
		if options.instance_id:		
			id = options.instance_id
			prepare_input(id,options.input_dir)
			run_task(id)
			get_output(id)
		else:
			parser.print_help()
	elif 'teardown' in args:
		if options.instance_id:
			id = options.instance_id
			destroy_environ(id)
		else:
			parser.print_help()
	else:
		parser.print_help()