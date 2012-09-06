from simplepackage import *
from optparse import OptionParser
import sys
import time
import logging


def start():

    #http://docs.python.org/howto/logging.html#logging-basic-tutorial
    logging.config.fileConfig('logging.conf')
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config_file = os.path.expanduser("~/.cloudenabling/config.sys")
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config_file = os.path.expanduser("config.sys")  # a default config file
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            logger.error("no configuration file found")
            sys.exit(1)

    environ_fields = ['USER_NAME', 'PASSWORD', 'PRIVATE_KEY',
                      'PAYLOAD_LOCAL_DIRNAME', 'PAYLOAD',
                      'DEST_PATH_PREFIX', 'DEPENDS', 'COMPILER',
                      'COMPILE_FILE', 'PAYLOAD_CLOUD_DIRNAME',
                      'SLEEP_TIME', 'RETRY_ATTEMPTS',
                      'OUTPUT_FILES', 'TEST_VM_IP',
                      'EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                      'CLOUD_SLEEP_INTERVAL', 'PRIVATE_KEY_NAME',
                      'SECURITY_GROUP']

    import json
    settings = type('', (), {})()
    for field in environ_fields:
        #TODO: add multiple sections
        val = config.get("basic", field)
        if '#' in val:  # remove comments
            val, _ = val.split('#', 1)
        try:
            field_val = json.loads(val)    # use JSON to parse values
        except ValueError, e:
            file_val = ""
        # and make fake object to hold them
        setattr(settings, field, field_val)
        logger.debug("%s" % field_val)

    # get command line options
    parser = OptionParser()
    parser.add_option("-n", "--nodeid", dest="instance_id",
                      help="The instance id from the cloud infrastructure")
    parser.add_option("-i", "--inputdir", dest="input_dir",
                      help="The local directory holding \
                      input files for the task")
    parser.add_option("-o", "--outputdir", dest="output_dir",
                      help="The local directory which will \
                      hold output files for the task")
    parser.add_option("-g", "--group", dest="group_id",
                      help="The group id from the cloud infrastructure")
    parser.add_option("-v", "--number-vm-instances",
                      dest="number_vm_instances",
                      help="The number of VM instances to " +
                      "be created as a group")
    parser.add_option("-s", "--seed", dest="seed",
                      help="The master seed that generates all other seeds")

    (options, args) = parser.parse_args()

    if 'create' in args:
        res = create_environ(settings)
        logger.debug(res)

    elif 'setup' in args:
        if options.instance_id:
            id = options.instance_id
            if not is_instance_running(id, settings):
                logging.error('Instance %s not running' % id)
                sys.exit(1)
            setup_task(id, settings)
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
            if not is_instance_running(id, settings):
                logging.error('Instance %s not running' % id)
                sys.exit(1)
            prepare_input(id, options.input_dir, settings)
            try:
                job_id = run_task(id, settings)
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package")
                #TODO: cleanup node of copied input files etc.
                sys.exit(1)
            logger.debug(job_id)
            if (len(job_id) != 1):
                logging.warn("warning: muliple payloads running")
            while (True):
                if job_finished(id, settings):
                    break
                print("job is running.  Wait or CTRL-C to exit here. \
                 run 'check' command to poll again")
                time.sleep(settings.SLEEP_TIME)
            if options.output_dir:
                print "done. output is available"
                get_output(id, options.output_dir, settings)
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
            if not is_instance_running(id, settings):
                logging.error('Instance %s not running' % id)
                sys.exit(1)

            if job_finished(options.instance_id, settings):
                print "done. output is available"
                get_output(id, options.output_dir, settings)
            else:
                print "job still running"
        else:
            logger.error("enter nodeid of the package")
            parser.print_help()
            sys.exit(1)

    elif 'teardown' in args:
        if options.instance_id:
            id = options.instance_id
            if not is_instance_running(id, settings):
                logging.error('Instance %s not running' % id)
                sys.exit(1)
            destroy_environ(id, settings)
        else:
            logger.error("enter nodeid of the package")
            parser.print_help()
            sys.exit(1)

    elif 'print' in args:
        print_running_node_id(settings)

    else:
        parser.print_help()


if __name__ == '__main__':
    start()
