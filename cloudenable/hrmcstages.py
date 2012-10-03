
# Contains the specific connectors and stages for HRMC

import os
import time
import logging
import logging.config
import json
import os

logger = logging.getLogger(__name__)


from smartconnector import Stage
from smartconnector import UI
from smartconnector import ParallelStage
from smartconnector import SequentialStage
from smartconnector import SmartConnector

from filesystem import FileSystem
from filesystem import DataObject


from cloudconnector import create_environ

from cloudconnector import get_rego_nodes
from cloudconnector import open_connection
from cloudconnector import get_instance_ip
from hrmcimpl import setup_multi_task
from hrmcimpl import prepare_multi_input

from hrmcimpl import run_command
from hrmcimpl import PackageFailedError
from hrmcimpl import run_multi_task
from hrmcimpl import _normalize_dirpath
from hrmcimpl import _status_of_nodeset
from hrmcimpl import is_instance_running
from hrmcimpl import job_finished


def get_elem(context,key):
    try:
        elem = context[key]
    except KeyError,e:
        logger.error("cannot load filesys %s from %s" % (e,context))
        return None
    return elem



def get_filesys(context):
    return get_elem(context,'filesys')


def get_file(fsys,file):
    try:
        config = fsys.retrieve(file)
    except KeyError,e:
        logger.error("cannot load %s %s" % (file,e))
        return {}
    return config


def get_settings(context):
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys, "default/config.sys")
    logger.debug("config= %s" % config)
    settings_text = config.retrieve()
    logger.debug("settings_text= %s" % settings_text)
    res = json.loads(settings_text)
    logger.debug("res=%s" % dict(res))
    return dict(res)


def get_run_info(context):
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys,"default/runinfo.sys")
    logger.debug("config= %s" % config)

    settings_text = config.retrieve()

    logger.debug("runinfo_text= %s" % settings_text)
    res = json.loads(settings_text)
    logger.debug("res=%s" % dict(res))
    return dict(res)


class Configure(Stage, UI):
    """
        - Load config.sys file into the filesystem
        - Nothing beyond specifying the path to config.sys
        - Later could be dialogue box,...
    """

    def triggered(self, context):
        return True

    def process(self, context):
        # - Load config.sys file into the filesystem
        # - Nothing beyond specifying the path to config.sys
        # - Later could be dialogue box,...
        # 1. creates instance of file system
        # 2. loads the content of config.sys to filesystem

        HOME_DIR = os.path.expanduser("~")
        local_filesystem = 'default'
        global_filesystem = os.path.expanduser("~")
        self.filesystem = FileSystem(global_filesystem, local_filesystem)

        #TODO: the path to the original config file should be
        # provided via command line or a web page.
        # For now, we assume, its location is 'original_config_file_path'
        #TODO: also need to load up all the input files
        original_config_file_path = HOME_DIR+"/sandbox/cloudenabling/cloudenable/config.sys.json"
        original_config_file = open(original_config_file_path, 'r')
        original_config_file_content = original_config_file.read()
        original_config_file.close()

        data_object =  DataObject("config.sys")
        data_object.create(original_config_file_content)
        self.filesystem.create(local_filesystem, data_object)


    # indicate the process() is completed
    def output(self, context):
        # store in filesystem
        # pass the file system as entry in the Context
        context = {'filesys':self.filesystem}
        return context

class Create(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        #check the context for existence of a file system
        if get_filesys(context):
            self.settings = get_settings(context)
            logger.debug("settings = %s" % self.settings)
            return True
        return False

    '''
        if True:
            self.settings = utility.load_generic_settings()
            return True

    def _transform_the_filesystem(filesystem, settings):
        key =  settings['ec2_access_key']

        print key
    '''

    def process(self, context):
        #user input
        number_vm_instances = 1
        self.seed = 32
        self.group_id = create_environ(number_vm_instances, self.settings)

    def output(self, context):
        # store in filesystem
        #self._store(self.temp_sys, filesystem)
        local_filesystem = 'default'
        data_object =  DataObject("runinfo.sys")
        data_object.create(json.dumps({'group_id':self.group_id, 'seed':self.seed}))


        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)

        return context


class Setup(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        # triggered if the set of the VMS has been established.
        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        self.packaged_nodes = get_rego_nodes(self.group_id, self.settings)
        logger.debug("packaged_nodes = %s" % self.packaged_nodes)

        return len(self.packaged_nodes)

    def process(self, context):
        setup_multi_task(self.group_id, self.settings)

    def output(self, context):

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys,"default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        config = json.loads(settings_text)
        config['setup_finished'] = len(self.packaged_nodes) # FIXME: possible race condition?
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)

        fsys.update("default", run_info_file)

        # FIXME: check to make sure not retriggered

        return context


class Run(Stage):
    """
    Start N nodes and return status
    """

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.

        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'setup_finished' in self.settings:
            setup_nodes = self.settings['setup_finished']
            logger.debug("setup_nodes = %s" % setup_nodes)
            packaged_nodes = len(get_rego_nodes(self.group_id, self.settings))
            logger.debug("packaged_nodes = %s" % packaged_nodes)
            if packaged_nodes == setup_nodes:
                return True
            else:
                logger.error("Indicated number of setup nodes does not match allocated number")
                logger.error("%s != %s" % (packaged_nodes, setup_nodes))
                return False
        else:
            logger.info("setup was not finished")
            return False


    def process(self, context):

        if 'seed' in self.settings:
            seed = self.settings['seed']
        else:
            seed = 42
            logger.warn("No seed specified. Using default value")

        # NOTE we assume that correct local file system has been created.

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        # expose subdirectory as filesystem for copying

        nodes = get_rego_nodes(self.group_id, self.settings)

        import random
        random.seed(seed)
        seeds = {}
        for node in nodes:
            # FIXME: is the random supposed to be positive or negative?
            seeds[node] = random.randrange(0,self.settings['MAX_SEED_INT'])

        if seed:
            print ("seed for full package run = %s" % seed)
        else:
            print ("seeds for each node in group %s = %s" % (self.group_id,[(x.name,seeds[x]) for x in seeds.keys()]))

        # input_dir is assumed to be populated.
        input_dir = "input"

        logger.debug("seeds = %s" % seeds)
        for node in nodes:
            instance_id = node.name
            logger.info("prepare_input %s %s" % (instance_id, input_dir))
            ip = get_instance_ip(instance_id, self.settings)
            ssh = open_connection(ip_address=ip, settings=self.settings)
            #ssh = open_connection(ip_address=ip, username=self.settings['USER_NAME'],
            #                       password=self.settings['PASSWORD'], settings=self.settings)

            #input_dir = _normalize_dirpath(input_dir)
            #dirList = os.listdir(input_dir)
            # for fname in dirList:
            #     logger.debug(fname)
            #     _upload_input(ssh, input_dir, fname,
            #                   os.path.join(settings['DEST_PATH_PREFIX'],
            #                                settings['PAYLOAD_CLOUD_DIRNAME']))

            fsys.upload_input(ssh, "input", os.path.join(self.settings['DEST_PATH_PREFIX'],
                                           self.settings['PAYLOAD_CLOUD_DIRNAME']))

            run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
                        (os.path.join(self.settings['DEST_PATH_PREFIX'],
                                      self.settings['PAYLOAD_CLOUD_DIRNAME'])))
            run_command(ssh, "cd %s; dos2unix rmcen.inp" %
                        (os.path.join(self.settings['DEST_PATH_PREFIX'],
                                      self.settings['PAYLOAD_CLOUD_DIRNAME'])))
            run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
                        (os.path.join(self.settings['DEST_PATH_PREFIX'],
                                      self.settings['PAYLOAD_CLOUD_DIRNAME'])))

            run_command(ssh, "cd %s; sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' rmcen.inp" %
                        (os.path.join(self.settings['DEST_PATH_PREFIX'],
                                      self.settings['PAYLOAD_CLOUD_DIRNAME']), seeds[node]))


        try:
            pids = run_multi_task(self.group_id, input_dir, self.settings)


        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages")
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)
        return pids


    def output(self, context):

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys,"default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        nodes = get_rego_nodes(self.group_id, self.settings)
        logger.debug("nodes = %s" % nodes)
        error_nodes = []
        finished_nodes = []

        for node in nodes:
            instance_id = node.name
            ip = get_instance_ip(instance_id, self.settings)
            ssh = open_connection(ip_address=ip, settings=self.settings)
            if not is_instance_running(instance_id, self.settings):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                logging.error('Instance %s not running' % instance_id)
                error_nodes.append(node)
                continue
            if job_finished(instance_id, self.settings):
                print "done. output is available"
                finished_nodes.append(node)
            else:
                print "job still running on %s: %s" % (instance_id,
                                               get_instance_ip(instance_id,
                                                            self.settings))

        # TODO: handle error_nodes
        logger.debug("finished = %s" % finished_nodes)
        logger.debug("error_nodes = %s" % error_nodes)
        nodes_working = len(nodes) - len(finished_nodes)
        config = json.loads(settings_text)
        config['runs_left'] = nodes_working # FIXME: possible race condition?
        config['error_nodes'] = len(error_nodes)
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        logger.debug("run_info_file=%s" % run_info_file)
        fsys.update("default", run_info_file)
        # FIXME: check to make sure not retriggered
        return context

class Finished(Stage):
    """
    Return whether the run has finished or not
    """

    def __init__(self):
        self.runs_left= 0
        self.error_nodes = 0

    def triggered(self, context):

        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.group_id = run_info['group_id']

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        return 'runs_left' in self.settings

    def process(self, context):

        self.nodes = get_rego_nodes(self.group_id, self.settings)

        self.error_nodes = []
        self.finished_nodes = []
        for node in nodes:
            instance_id = node.name
            if not is_instance_running(instance_id, self.settings):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                logging.error('Instance %s not running' % instance_id)
                self.error_nodes.append(node)
                continue
            if job_finished(instance_id, self.settings):
                print "done. output is available"
                download_output(ssh, instance_id, "output", self.settings)
                self.finished_nodes.append(node)
            else:
                print "job still running on %s: %s" % (instance_id,
                                               get_instance_ip(instance_id,
                                                            settings))

    def output(self, context):
        nodes_working = len(self.nodes) - len(self.finished_nodes)
        config = json.loads(settings_text)
        if nodes_working:
            config['runs_left'] = nodes_working # FIXME: possible race condition?
            config['error_nodes'] = len(self.error_nodes)
        else:
            del config['runs_left']
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        logger.debug("run_info_file=%s" % run_info_file)
        fsys.update("default", run_info_file)
        return context


class Converge(Stage):
    """
    Return whether the run has finished or not
    """
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']
        pass

    def process(self, context):
        pass

    def output(self, context):
        pass





class Transform(Stage):
    """
    Return whether the run has finished or not
    """
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']
        pass

    def process(self, context):
        pass

    def output(self, context):
        pass




class Teardown(Stage):
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']

    def process(self, context):
        pass

    def output(self, context):
        pass



def mainloop():

# load system wide settings, e.g Security_Group
#communicating between stages: crud context or filesystem
#build context with file system as its only entry
    context = {}
    #context['version'] = "1.0.0"


    #filesys.update_file('Butini')
    #filesys.delete_file(path_fs, 'Iman')

    #filesys.create_initial_filesystem()
    #filesys.load_generic_settings()

    smart_conn = SmartConnector()
    #stage= Configure()
    #smart_conn.register(Configure())
    #smart_conn.register(Create())

    for stage in (Configure(), Create(), Setup(),Run(), Finished()):#, Check(), Teardown()):
        smart_conn.register(stage)


    #print smart_con.stages

    #while loop is infinite:
    # check the semantics for 'dropping data' into
    # designated location.
    #What happens if data is dropped while
    #another is in progress?


    #while(True):

    while (True):
        done = 0
        for stage in smart_conn.stages:
            print "Working in stage",stage
            if stage.triggered(context):
                stage.process(context)
                context = stage.output(context)
                logger.debug("Context", context)
                done += 1
                #smart_con.unregister(stage)
                #print "Deleting stage",stage
            logger.debug(done, " ", len(smart_conn.stages))

        if done == len(smart_conn.stages):
            break

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    begins = time.time()
    mainloop()
    ends = time.time()
    print "Total execution time: %d seconds" % (ends-begins)

