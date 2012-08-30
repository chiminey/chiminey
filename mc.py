from cloudenable.simplepackage import *
from optparse import OptionParser
import settings
import sys      
import time
import logging



if __name__ == '__main__':

    #http://docs.python.org/howto/logging.html#logging-basic-tutorial
    logging.config.fileConfig('logging.conf')


    # There are four main paths at the moment.
    # 1) Create a instance 
    # 2) Set up the instance with task package installed
    # 3) Provide input, run task and retrieve output
    # 4) Destroy the instance.
    # This is because we may want to run the sequence 1,2,2,2,3

    # get command line options

    parser = OptionParser()
    parser.add_option("-n", "--nodeid",dest="instance_id",
	                  help="The instance id from the cloud infrastructure")
    parser.add_option("-i", "--inputdir", dest="input_dir",
	                  help="The local directory holding input files for the task")		
    parser.add_option("-o", "--outputdir", dest="output_dir",
	                  help="The local directory which will hold output files for the task")	

    (options, args) = parser.parse_args()

    if 'create' in args:
		logger.debug(create_environ())

    elif 'setup' in args:
		if options.instance_id:
			id = options.instance_id
			if not is_instance_running (id):
				logging.error ('Instance %s not running' %id)
				sys.exit(1)

			setup_task(id)
		else:
			logging.error("enter nodeid of the package")
			parser.print_help()
			sys.exit(1)
        
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
			if not is_instance_running (id):
				logging.error ('Instance %s not running' %id)
				sys.exit(1)

			prepare_input(id,options.input_dir)
			try:
				job_id = run_task(id)	
			except PackageFailedError, e:
				logger.error(e)
				logger.error("unable to start package")
				#TODO: cleanup node of copied input files etc.
				sys.exit(1)	
			
			logger.debug(job_id)
			if (len(job_id) != 1):
				logging.warn("warning: muliple payloads running")
			while (True):
				if job_finished(id):
					break
				print("job is running.  Wait or CTRL-C to exit here.  run 'check' command to poll again")
				time.sleep(settings.SLEEP_TIME)
			if options.output_dir:	
				print "done. output is available"		
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
			if not is_instance_running (id):
				logging.error ('Instance %s not running' %id)
				sys.exit(1)

			if job_finished(options.instance_id):
				print "done. output is available"	
				get_output(id,options.output_dir)
			else: 
				print "job still running"
		else:
			logger.error("enter nodeid of the package")
			parser.print_help() 
			sys.exit(1)

    elif 'teardown' in args:
        	if options.instance_id:
            		id = options.instance_id
            		if not is_instance_running (id):
						logging.error ('Instance %s not running' %id)
						sys.exit(1)

            		destroy_environ(id)
        	else:
            		logger.error("enter nodeid of the package")
            		parser.print_help()
            		sys.exit(1)
    else:
		parser.print_help()
