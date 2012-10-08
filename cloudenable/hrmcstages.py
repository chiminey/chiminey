# Copyright (C) 2012, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

# Contains the specific connectors and stages for HRMC

import time
import logging
import logging.config
import json
import os
import sys

logger = logging.getLogger(__name__)


from smartconnector import Stage
from smartconnector import UI
from smartconnector import SmartConnector

from filesystem import FileSystem
from filesystem import DataObject

from cloudconnector import create_environ
from cloudconnector import get_rego_nodes
from cloudconnector import open_connection
from cloudconnector import get_instance_ip
from cloudconnector import collect_instances
from cloudconnector import destroy_environ

from hrmcimpl import setup_multi_task
#from hrmcimpl import prepare_multi_input

from hrmcimpl import run_command
from hrmcimpl import PackageFailedError
from hrmcimpl import run_multi_task
#from hrmcimpl import _normalize_dirpath
#from hrmcimpl import _status_of_nodeset
from hrmcimpl import is_instance_running
from hrmcimpl import job_finished


def get_elem(context, key):
    try:
        elem = context[key]
    except KeyError, e:
        logger.error("cannot load elem %s from %s" % (e, context))
        return None
    return elem


def get_filesys(context):
    """
    Return the filesys in the context
    """
    return get_elem(context, 'filesys')


def get_file(fsys, file):
    """
    Return contents of file
    """
    try:
        config = fsys.retrieve(file)
    except KeyError, e:
        logger.error("cannot load %s %s" % (file, e))
        return {}
    return config


def get_settings(context):
    """
    Return contents of config.sys file as a dictionary
    """
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys, "default/config.sys")
    logger.debug("config= %s" % config)
    settings_text = config.retrieve()
    logger.debug("settings_text= %s" % settings_text)
    res = json.loads(settings_text)
    logger.debug("res=%s" % dict(res))
    return dict(res)


def get_run_info_file(context):
    """
    Returns the actual runinfo file. If problem, return None
    """
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys, "default/runinfo.sys")
    logger.debug("config= %s" % config)
    return config


def get_run_info(context):
    """
    Returns the content of the run info file as a dict. If problem, return None
    """
    fsys = get_filesys(context)

    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys, "default/runinfo.sys")
    logger.debug("config= %s" % config)
    if config:
        settings_text = config.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)
        res = json.loads(settings_text)
        logger.debug("res=%s" % dict(res))
        return dict(res)
    return None


class Configure(Stage, UI):
    """
        - Load config.sys file into the filesystem
        - Nothing beyond specifying the path to config.sys
        - Later could be dialogue box,...
    """

    def triggered(self, context):
        """
        True if filesystem exists in context
        """
        if not get_filesys(context):
            return True
        return False

    def process(self, context):
        """
        Create config file
        """
        # - Load config.sys file into the filesystem
        # - Nothing beyond specifying the path to config.sys
        # - Later could be dialogue box,...
        # 1. creates instance of file system
        # 2. loads the content of config.sys to filesystem

        HOME_DIR = os.path.expanduser("~")
        local_filesystem = 'default'
        global_filesystem = os.path.join(HOME_DIR, "testStages")
        self.filesystem = FileSystem(global_filesystem, local_filesystem)

        #TODO: the path to the original config file should be
        # provided via command line or a web page.
        # For now, we assume, its location is 'original_config_file_path'
        #TODO: also need to load up all the input files
        original_config_file_path = os.path.join(
            HOME_DIR,
            "sandbox/cloudenabling",
            "cloudenable/config.sys.json")
        original_config_file = open(original_config_file_path, 'r')
        original_config_file_content = original_config_file.read()
        original_config_file.close()

        data_object = DataObject("config.sys")
        data_object.create(original_config_file_content)
        self.filesystem.create(local_filesystem, data_object)

    # indicate the process() is completed
    def output(self, context):
        """
        Store ref to filesystem in context
        """
        # store in filesystem
        # pass the file system as entry in the Context
        context = {'filesys': self.filesystem}
        return context


class Create(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        """
        Return True if there is a file system but it doesn't contain run_info file.
        """
        if get_filesys(context):
            if not get_run_info(context):
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
        """
        Make new VMS and store group_id
        """

        #TODO: user input of this information
        number_vm_instances = 1
        self.seed = 32
        self.group_id = create_environ(number_vm_instances, self.settings)

    def output(self, context):
        """
        Create a runfinos.sys file in filesystem with new group_id
        """
        # store in filesystem
        #self._store(self.temp_sys, filesystem)
        local_filesystem = 'default'
        data_object = DataObject("runinfo.sys")
        data_object.create(json.dumps({'group_id': self.group_id,
                                       'seed': self.seed}))

        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)

        return context


class Setup(Stage):
    """
    Handles creation of a running executable on the VMS in a group
    """

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        """
        Triggered if appropriate vms exist and we have not finished setup
        """
        # triggered if the set of the VMS has been established.
        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        #FIXME: need to check for no group_id which can happen when over quota

        if 'setup_finished' in self.settings:
            return False

        self.packaged_nodes = get_rego_nodes(self.group_id, self.settings)
        logger.debug("packaged_nodes = %s" % self.packaged_nodes)

        return len(self.packaged_nodes)

    def process(self, context):
        """
        Setup all the nodes
        """
        setup_multi_task(self.group_id, self.settings)

    def output(self, context):
        """
        Store number of packages nodes as setup_finished in runinfo.sys
        """

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        config = json.loads(settings_text)
        config['setup_finished'] = len(self.packaged_nodes)  # FIXME: possible race condition?
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)

        fsys.update("default", run_info_file)

        return context


class Run(Stage):
    """
    Start applicaiton on nodes and return status
    """

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.

        # input_dir is assumed to be populated.

        if 'id' in context:
            self.id = context['id']
            self.input_dir = "input_%s" % self.id
        else:
            self.input_dir = "input"
        print "Run stage triggered"
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

            if 'runs_left' in self.settings:
                return False

            if packaged_nodes == setup_nodes:
                return True
            else:
                logger.error("Indicated number of setup nodes does not match allocated number")
                logger.error("%s != %s" % (packaged_nodes, setup_nodes))
                return False
        else:
            logger.info("setup was not finished")
            return False

    def _create_input(self, instance_id, seeds, node, fsys):
        ip = get_instance_ip(instance_id, self.settings)
        ssh = open_connection(ip_address=ip, settings=self.settings)
        fsys.upload_input(ssh, self.input_dir, os.path.join(
            self.settings['DEST_PATH_PREFIX'],
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

    def _prepare_input(self, context):
        """
        Copy the input parameters for the package to the VM
        """

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        if 'seed' in self.settings:
            seed = self.settings['seed']
        else:
            seed = 42
            logger.warn("No seed specified. Using default value")
        # NOTE we assume that correct local file system has been created.

        import random
        random.seed(seed)

        seeds = {}

        # expose subdirectory as filesystem for copying

        nodes = get_rego_nodes(self.group_id, self.settings)

        for node in nodes:
            # FIXME: is the random supposed to be positive or negative?
            seeds[node] = random.randrange(0, self.settings['MAX_SEED_INT'])

        if seed:
            print ("seed for full package run = %s" % seed)
        else:
            print ("seeds for each node in group %s = %s"
                   % (self.group_id, [(x.name, seeds[x])
                         for x in seeds.keys()]))

        logger.debug("seeds = %s" % seeds)

        for node in nodes:
            instance_id = node.name
            logger.info("prepare_input %s %s" % (instance_id, self.input_dir))

            self._create_input(instance_id, seeds, node, fsys)

    def process(self, context):

        self._prepare_input(context)

        try:
            pids = run_multi_task(self.group_id, self.input_dir, self.settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages")
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)
        return pids

    def output(self, context):
        """
        Assume that no nodes have finished yet and indicate to future stages
        """
        #TODO: make function for get fsys, run_info and settings
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        nodes = get_rego_nodes(self.group_id, self.settings)
        logger.debug("nodes = %s" % nodes)

        config = json.loads(settings_text)
        # We assume that none of runs have finished yet.
        config['runs_left'] = len(nodes)  # FIXME: possible race condition?
        #config['error_nodes'] = len(error_nodes)
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
        self.runs_left = 0
        self.error_nodes = 0

    def triggered(self, context):
        """
        Checks whether there is a non-zero number of runs still going.
        """

        if 'id' in context:
            self.id = context['id']
            self.output_dir = "output_%s" % self.id
        else:
            self.output_dir = "output"

        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)
        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)
        self.group_id = run_info['group_id']
        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)
        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        # if we have no runs_left then we must have finished all the runs
        if 'runs_left' in self.settings:
            return self.settings['runs_left']
        return False

    def process(self, context):
        """
        Check all registered nodes to find whether they are running, stopped or in error_nodes
        """

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        self.nodes = get_rego_nodes(self.group_id, self.settings)

        self.error_nodes = []
        self.finished_nodes = []
        for node in self.nodes:

            instance_id = node.name
            ip = get_instance_ip(instance_id, self.settings)
            ssh = open_connection(ip_address=ip, settings=self.settings)
            if not is_instance_running(instance_id, self.settings):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                #FIXME: should error nodes be counted as finished?
                logging.error('Instance %s not running' % instance_id)
                self.error_nodes.append(node)
                continue
            fin = job_finished(instance_id, self.settings)
            logger.debug("fin=%s" % fin)
            if fin:
                print "done. output is available"

                logger.debug("node=%s" % node)
                logger.debug("finished_nodes=%s" % self.finished_nodes)
                #FIXME: for multiple nodes, if one finishes before the other then
                #its output will be retrieved, but it may again when the other node fails, because
                #we cannot tell whether we have prevous retrieved this output before and finished_nodes
                # is not maintained between triggerings...
                if not (node.name in [x.name for x in self.finished_nodes]):
                    fsys.download_output(ssh, instance_id, self.output_dir, self.settings)
                else:
                    logger.info("We have already "
                        + "processed output from node %s" % node.name)
                self.finished_nodes.append(node)
            else:
                print "job still running on %s: %s" % (instance_id,
                                               get_instance_ip(instance_id,
                                                            self.settings))

    def output(self, context):
        """
        Output new runs_left value (including zero value)
        """
        nodes_working = len(self.nodes) - len(self.finished_nodes)

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        config = json.loads(settings_text)
        config['runs_left'] = nodes_working  # FIXME: possible race condition?
        config['error_nodes'] = len(self.error_nodes)
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        logger.debug("run_info_file=%s" % run_info_file)
        fsys.update("default", run_info_file)

        # NOTE: runs_left cannot be deleted or run() will trigger
        return context

    def _kill_run(context):
        """ Based on information from the current run, decide whether to kill the current runs
        """
        #TODO:
        pass


class Converge(Stage):
    """
    Determine whether the function has been optimised
    """
    def __init__(self, number_of_iterations):
        self.total_iterations = number_of_iterations
        self.number_of_remaining_iterations = number_of_iterations

    def triggered(self, context):

        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        if 'runs_left' in self.settings:
            self.run_list = self.settings["runs_left"]
            if self.run_list == 0:
                return True
        return False

    def process(self, context):
        self.number_of_remaining_iterations -= 1
        print "Number of Iterations Left %d" % self.number_of_remaining_iterations

        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        config = json.loads(settings_text)
        del(config['runs_left'])
        del(config['error_nodes'])  # ??
        logger.debug("config=%s" % config)

        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        logger.debug("run_info_file=%s" % run_info_file)
        fsys.update("default", run_info_file)

    def output(self, context):
        fsys = get_filesys(context)
        run_info_file = get_file(fsys, "default/runinfo.sys")
        settings_text = run_info_file.retrieve()
        config = json.loads(settings_text)
        config['converged'] = False
        if self.number_of_remaining_iterations == 0:
            config['converged'] = True
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        fsys.update("default", run_info_file)
        return context


class Transform(Stage):
    """
    Convert output into input for next iteration.
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
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        if 'converged' in self.settings:
            if self.settings['converged'] == True:
                if not 'run_finished' in self.settings:
                    return True
        return False
        #trigger_message = self.settings["setup_finished"]

        #trigger message should be changed
        '''
        try:
            trigger_message = self.settings["setup_finished"]
            return True
        except:
            return False
        '''
    def process(self, context):
        all_instances = collect_instances(self.settings, group_id=self.group_id)
        destroy_environ(self.settings, all_instances)

    def output(self, context):
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)

        config = json.loads(settings_text)
        config['run_finished'] = True  # FIXME: possible race condition?
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)

        fsys.update("default", run_info_file)

        # FIXME: check to make sure not retriggered

        return context  # self.packaged_nodes


class Sleep(Stage):
    """
    Go to sleep
    """

    def __init__(self, secs):
        self.sleeptime = secs

    def triggered(self, context):
        # FIXME: broken because dispatch loop will never exit because
        # stage will always trigger.  Need to create return state that
        # triggers dispatch loop to end
        return True

    def process(self, context):
        pass

    def output(self, context):
        context['Done'] = True
        return context


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

    number_of_iterations = 2
    smart_conn = SmartConnector()
    #stage= Configure()
    #smart_conn.register(Configure())
    #smart_conn.register(Create())

    for stage in (Configure(), Create(), Setup(), Run(), Finished(),
        Converge(number_of_iterations), Teardown()):  # , Check(), Teardown()):
    #for stage in (Configure(), Create(), Teardown()):#, Run(), Check(), Teardown()):
        smart_conn.register(stage)

    #print smart_con.stages

    #while loop is infinite:
    # check the semantics for 'dropping data' into
    # designated location.
    #What happens if data is dropped while
    #another is in progress?

    #while(True):
    #smart_conn = SmartConnector()

    #smart_conn.register(Converge())

    while (True):
        done = 0
        not_triggered = 0
        for stage in smart_conn.stages:
            print "Working in stage %s" % stage
            if stage.triggered(context):
                stage.process(context)
                context = stage.output(context)
                logger.debug("Context", context)
            else:
                not_triggered += 1
                #smart_con.unregister(stage)
                #print "Deleting stage",stage
                print context
            logger.debug(done, " ", len(smart_conn.stages))

        if not_triggered == len(smart_conn.stages):
            break

    '''
    exit_reached = False
    while (True):
        done = 0
        not_triggered = 0
        for stage in smart_conn.stages:
            print "Working in stage",stage
            if stage.triggered(context):
                stage.process(context)
                context = stage.output(context)
                logger.debug("Context", context)
                if type(stage==Teardown):
                    print "exit_reached"
                    exit_reached = True
            else:
                not_triggered += 1
                #smart_con.unregister(stage)
                #print "Deleting stage",stage
                print context
            logger.debug(done, " ", len(smart_conn.stages))

        if exit_reached:
            break
        else:
            print "Not Teardown"
    '''

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    begins = time.time()
    mainloop()
    ends = time.time()
    print "Total execution time: %d seconds" % (ends-begins)

