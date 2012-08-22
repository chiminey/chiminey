from cloudenable.simplepackage import *
from optparse import OptionParser
import settings
import sys		
import time
import logging



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
	parser.add_option("-o", "--outputdir", dest="output_dir",
	                  help="The local directory which will hold output files for the task")	

	(options, args) = parser.parse_args()

	if 'setup' in args:
		print create_environ()	
	elif 'run' in args:
		if options.instance_id:		
			if not options.output_dir:
				logging.error("need to specify output directory")
				parser.print_help()
				sys.exit(1)
			elif os.path.isdir(options.output_dir):
				logging.error("output directory already exists")
				sys.exit(1)				
			id = options.instance_id
			prepare_input(id,options.input_dir)
			job_id = run_task(id)	
			print job_id	
			if (len(job_id) != 1):
				logging.warn("warning: muliple payloads running")
			while (True):
				if job_finished(id):
					break
				logging.info("job is running.  Wait or CTRL-C to exit here.  run 'check' command to poll again")
				time.sleep(settings.SLEEP_TIME)
			if options.output_dir:			
				get_output(id,options.output_dir)
			else:
				logging.error("need to specify output directory")
				parser.print_help()
				sys.exit(1)
		else:
			logging.error("enter nodeid of the package")
			parser.print_help()
			sys.exit(1)

	elif 'check' in args:
		if options.instance_id:
			if not options.output_dir:
				logging.error("need to specify output directory")
				parser.print_help()
				sys.exit(1)
			elif os.path.isdir(options.output_dir):			
					logging.error("output directory already exists")
					sys.exit(1)	
			id = options.instance_id
			if job_finished(options.instance_id):
				print "done"	
				get_output(id,options.output_dir)
		else:
			print "enter nodeid of the package"		
			parser.print_help() 
			sys.exit(1)
	elif 'teardown' in args:
		if options.instance_id:
			id = options.instance_id
			destroy_environ(id)
		else:
			print "enter nodeid of the package"
			parser.print_help()
			sys.exit(1)
	else:
		parser.print_help()

