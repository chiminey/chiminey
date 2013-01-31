from optparse import OptionParser
import sys
import os
import time
import logging
import logging.config


from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, collect_instances, print_all_information, confirm_teardown, destroy_environ, get_ids_of_instances

from bdphpcprovider.smartconnectorscheduler.hrmcimpl import prepare_multi_input, setup_multi_task, run_multi_task, packages_complete, PackageFailedError



from smartconnector import SmartConnector
from hrmcstages import Configure
from hrmcstages import Create
from stages.setup import Setup
from hrmcstages import Run
from hrmcstages import Finished
#from hrmcstages import Converge
from hrmcstages import Teardown
from hrmcstages import clear_temp_files

logger = logging.getLogger(__name__)


def start(args):

    #http://docs.python.org/howto/logging.html#logging-basic-tutorial
    #logging.config.fileConfig('logging.conf')
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config_file = os.path.expanduser("~/.cloudenabling/config.sys")
    config_file="/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/config.sys"
    if os.path.exists(config_file):
        print "here"
        config.read(config_file)
    else:
        config_file = "/home/iman/cloudenabling/bdphpcprovider/smartconnectorscheduler/config.sys"  # a default config file
        print "there"
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            logger.error("no configuration file found")
            sys.exit(1)

    environ_fields = ['USER_NAME', 'PASSWORD', 'PRIVATE_KEY',
                      'VM_SIZE', 'VM_IMAGE',
                      'PAYLOAD_LOCAL_DIRNAME', 'PAYLOAD',
                      'DEST_PATH_PREFIX', 'DEPENDS', 'COMPILER',
                      'COMPILE_FILE', 'PAYLOAD_CLOUD_DIRNAME',
                      'SLEEP_TIME', 'RETRY_ATTEMPTS',
                      'OUTPUT_FILES', 'TEST_VM_IP',
                      'EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                      'CLOUD_SLEEP_INTERVAL', 'PRIVATE_KEY_NAME',
                      'SECURITY_GROUP', 'GROUP_ID_DIR', 'MAX_SEED_INT',
                      'PROVIDER', 'CUSTOM_PROMPT',
                      'POST_PROCESSING_LOCAL_PATH', 'POST_PAYLOAD',
                      'POST_PROCESSING_DEST_PATH_PREFIX','POST_PAYLOAD_COMPILE_FILE',
                      'POST_PAYLOAD_CLOUD_DIRNAME',
                      'PAYLOAD_SOURCE', 'PAYLOAD_DESTINATION']

    #['CUSTOM_PROMPT'] "[smart-connector_prompt]$"
    import json
    #settings = type('', (), {})()
    settings = {}
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
        settings[field]=field_val
        #setattr(settings, field, field_val)
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
    parser.add_option("-v", "--number-vm-instances", type="int",
        dest="number_vm_instances",
        help="The number of VM instances to " +
             "be created as a group")
    parser.add_option("-s", "--seed", dest="seed",
        help="The master seed that generates all other seeds")


    (options, args) = parser.parse_args(args)

    if 'smart' in args:
        context = {'number_vm_instances': 1}
        context['seed'] = 32
        context['group_id'] = "bf16c62b1927e100a10922ef36bce5e8"

        HOME_DIR = os.path.expanduser("~")
        global_filesystem = os.path.join(HOME_DIR, "testStages")
        context['global_filesystem'] = global_filesystem
        context['provider'] = 'nectar'

        if context['provider'].lower() == 'nectar':
            context['config.sys'] = "./config.sys.json"
        elif context['provider'].lower() == 'amazon':
            context['config.sys'] =  "./config.sys.json.ec2"
        else:
            print "unknown cloud service provider"
            sys.exit()

        number_of_iterations = 1
        smart_conn = SmartConnector()

        #for stage in (Configure(), Setup() ):#Create () Setup(), Run(), Finished(), Converge(number_of_iterations)):#, Teardown()):#, Check(), Teardown()):
        #for stage in (Configure(), Transform()):
         #   smart_conn.register(stage)

        smart_conn.register(Configure())
        smart_conn.register(Setup())
        #while loop is infinite:
        # check the semantics for 'dropping data' into
        # designated location.
        #What happens if data is dropped while
        #another is in progress?
        while (True):
            print "Loop started"
            done = 0
            not_triggered = 0
            for stage in smart_conn.stages:
                print "Working in stage", stage
                if stage.triggered(context):
                    stage.process(context)
                    context = stage.output(context)
                    logger.debug("Context %s" % context)
                else:
                    not_triggered += 1
                    #smart_con.unregister(stage)
                    #print "Deleting stage",stage
                    print context
                logger.debug(done, " ", len(smart_conn.stages))

            if not_triggered == len(smart_conn.stages):
                break

        #clear_temp_files(context)




    elif 'create' in args:
        if options.number_vm_instances:
            res = create_environ(options.number_vm_instances, settings)
            logger.debug(res)
            return res
        else:
            logging.error("enter number of VM instances to be created")
            parser.print_help()
            sys.exit(1)

    elif 'setup' in args:
        if options.group_id:
            group_id = options.group_id
            Setup().setup(settings, group_id)

            #setup_multi_task(group_id, settings)
        else:
            logging.error("enter nodeid of the package")
            parser.print_help()
            sys.exit(1)


    elif 'run' in args:
        if options.group_id:

            group_id = options.group_id

            if not options.output_dir:
                logging.error("specify output directory")
                parser.print_help()
                sys.exit(1)
            elif os.path.isdir(options.output_dir):
                logging.error("output directory already exists")
                sys.exit(1)
            else:
                try:
                    os.mkdir(options.output_dir)
                except OSError:
                    logger.error("output directory %s already exists" % options.output_dir)
                    sys.exit(1)

            prepare_multi_input(group_id, options.input_dir,
                settings, options.seed)

            try:
                pids = run_multi_task(group_id, options.input_dir, settings)
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start packages")
                #TODO: cleanup node of copied input files etc.
                sys.exit(1)

            while (not packages_complete(group_id,
                options.output_dir,
                settings)):
                print("job is running.  Wait or CTRL-C to exit here. \
                 run 'check' command to poll again")
                time.sleep(settings['SLEEP_TIME'])

        else:
            logging.error("enter group id of the run")
            parser.print_help()
            sys.exit(1)

    elif 'check' in args:
        if options.group_id:
            if not options.output_dir:
                logging.error("specify output directory")
                parser.print_help()
                sys.exit(1)

            group_id = options.group_id
            is_finished = packages_complete(group_id,
                options.output_dir,
                settings)

            if is_finished:
                print "done. output is available at %s" % options.output_dir
                return 'DONE'
            else:
                print "job still running"
                return 'RUNNING'
        else:
            logger.error("enter group id of the run")
            parser.print_help()
            sys.exit(1)

    elif 'teardown' in args or 'teardown_all' in args:
        # TODO: make sure that the instance we are tearing down is the one
        # that is running the package and no some random VM, probably by
        # logging in and checking state.

        #TODO: refactor the following if, elif else statements

        if options.group_id:
            all_instances = collect_instances(settings, group_id=options.group_id)
            ids_of_instances = get_ids_of_instances(all_instances)
            confirm = True
            if not "yes" in args:
                confirm = confirm_teardown(settings, all_instances)
            if confirm:
                destroy_environ(settings, all_instances, ids_of_instances)
        elif options.instance_id:
            all_instances = collect_instances(settings, instance_id=options.instance_id)
            confirm = True
            if not "yes" in args:
                confirm = confirm_teardown(settings, all_instances)
            if confirm:
                destroy_environ(settings, all_instances, options.instance_id)
        elif 'teardown_all' in args:
            all_instances = collect_instances(settings, all_VM=True)
            ids_of_instances = get_ids_of_instances(all_instances)
            confirm = True
            if not "yes" in args:
                confirm = confirm_teardown(settings, all_instances)
            if confirm:
                destroy_environ(settings, all_instances, ids_of_instances)
        else:
            logger.error("Enter either group id or instance id of the package")
            parser.print_help()
            sys.exit(1)

        #    elif 'print' in args:
        #        print_running_node_id(settings)

    elif 'info' in args:
        print "Summary of Computing Environment"
        all_instances = collect_instances(settings, all_VM=True)
        print_all_information(settings, all_instances)
    else:
        parser.print_help()


if __name__ == '__main__':
    begins = time.time()
    start(sys.argv[1:])
    ends = time.time()
    logger.info("Total execution time: %d seconds" % (ends - begins))
