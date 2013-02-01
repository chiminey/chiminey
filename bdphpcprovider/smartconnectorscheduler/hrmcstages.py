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

import sys
import os
import time
import logging
import logging.config
import json
import os
import sys
import re

logger = logging.getLogger(__name__)


from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI, SmartConnector

from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject

from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, open_connection, collect_instances, destroy_environ
from bdphpcprovider.smartconnectorscheduler import botocloudconnector


from bdphpcprovider.smartconnectorscheduler.hrmcimpl import setup_multi_task, PackageFailedError, run_multi_task, job_finished
#from hrmcimpl import prepare_multi_input
#from hrmcimpl import _normalize_dirpath
#from hrmcimpl import _status_of_nodeset
from bdphpcprovider.smartconnectorscheduler.sshconnector import find_remote_files, run_command


def get_elem(context, key):
    try:
        elem = context[key]
    except KeyError, e:
        logger.error("cannot load element %s from %s" % (e, context))
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
    #logger.debug("config= %s" % config)
    settings_text = config.retrieve()
    #logger.debug("settings_text= %s" % settings_text)
    res = json.loads(settings_text)
    #logger.debug("res=%s" % dict(res))
    settings = dict(res)
    return settings


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


def get_run_settings(context):
    settings = get_settings(context)
    run_info = get_run_info(context)
    settings.update(run_info)
    settings.update(context)
    return settings


def update_key(key, value, context):
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = get_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    logger.debug("removing %s" % key)
    settings[key] = value  # FIXME: possible race condition?
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)


def delete_key(key, context):
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = get_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    del settings[key]
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)


def clear_temp_files(context):
    """
    Deletes temporary files
    """
    filesystem = get_filesys(context)
    print "Deleting temporary files ..."
    filesystem.delete_local_filesystem('default')
    print "done."


class Configure(Stage, UI):
    """
        - Creates file system,
        - Loads config.sys file into the filesystem,
        - Stores a reference to the filesystem in dictionary
    """
    def triggered(self, context):
        """
        True if filesystem does not exist in context
        """
        if not get_filesys(context):
            return True
        return False

    def process(self, context):
        """
        Create global filesystem and then load config.sys to the filesystem
        """
        global_filesystem = context['global_filesystem']
        local_filesystem = 'default'
        self.filesystem = FileSystem(global_filesystem, local_filesystem)

        original_config_file_path = context['config.sys']
        original_config_file = open(original_config_file_path, 'r')
        original_config_file_content = original_config_file.read()
        original_config_file.close()

        data_object = DataObject("config.sys")
        data_object.create(original_config_file_content)
        self.filesystem.create(local_filesystem, data_object)

    def output(self, context):
        """
        Store ref to filesystem in context
        """
        context['filesys'] = self.filesystem
        return context


class Schedule(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        """
            Return True if there is a file system
            but it doesn't contain run_info file.
        """

        if get_filesys(context):
            try:
                get_run_info(context)
            except IOError:
                self.settings = get_settings(context)
                logger.debug("settings = %s" % self.settings)
                return True
        return False

    def process(self, context):
        """ Determine the provider
        """
        questions = [
            ('architecture', "What is the architecture of the computation?", ['Embarrassingly_parallel', 'MapReduce', 'Other']),
            ('size', "How big is the computation", ['small', 'large']),
            ('sensitivity', 'What is the sensitivity of the data of the computation to location?', ['none', 'sensitive'])]

        self.answers = []
        for (quest_num, (question_name, question_desc, question_choices)) in enumerate(questions):
            print "Question %d: %s\n%s\n" % (quest_num + 1, question_name, question_desc)

            valid_input = False
            number_of_fails = 0
            while (not valid_input):
                for (choice_num, choice) in enumerate(question_choices):
                    print "%d %s" % (choice_num + 1, choice)

                input = raw_input("Enter choice: ")
                print input
                mychoice = ""
                try:
                    mychoice = int(input)
                except ValueError as e:
                    print "Invalid input: %s" % e
                    number_of_fails += 1
                else:
                    if mychoice in range(1, len(question_choices) + 1):
                        valid_input = True
                    else:
                        print "Please type number of answer: %s" % mychoice
                        number_of_fails += 1

            self.answers.append(int(mychoice))

        user_requirement = []
        question_no = 0
        for (quest_num, (question_name, question_desc, question_choices)) in enumerate(questions):
            logger.debug("Quest num %d, question name %s " % (quest_num, question_name))
            answer_index = self.answers[quest_num] - 1
            requirement = question_name + '=>' + question_choices[answer_index]
            user_requirement.append(requirement)
            logger.debug("req %s" % requirement)
        logger.debug(user_requirement)

        import DecisionTree
        training_datafile = './smartconnectorscheduler/provider_training.dat'
        dt = DecisionTree.DecisionTree(training_datafile=training_datafile,
                                entropy_threshold=0.1,
                                max_depth_desired=3,
                                debug1=1,
                                debug2=1
                              )
        dt.get_training_data()
        root_node = dt.construct_decision_tree_classifier()
        #   UNCOMMENT THE FOLLOWING LINE if you would like to see the decision
        #   tree displayed in your terminal window:
        #logger.debug(root_node.display_decision_tree("   "))
        classification = dt.classify(root_node, user_requirement)
        max_prob = self._get_highest_probability(classification)
        self.candidate_providers = self._get_candidate_providers(classification, max_prob)
        logger.debug("answers %s" % self.answers)

        return self.answers

    def _get_highest_probability(self, classification):
        which_classes = list(classification.keys())
        max_prob = 0
        for provider in which_classes:
            curr_prob = classification[provider]
            logger.debug("provider %s prob  %f" % (provider, curr_prob))
            if curr_prob > max_prob:
                max_prob = curr_prob
        return max_prob

    def _get_candidate_providers(self, classification, max_prob):
        which_classes = list(classification.keys())
        candidate_providers = []
        for provider in which_classes:
            curr_prob = classification[provider]
            if curr_prob == max_prob:
                candidate_providers.append(provider)
                logger.debug("Candidate provider %s " % provider)
        return candidate_providers

    def output(self, context):
        """
        Create a runfinos.sys file in filesystem with provider
        """
        self.provider = self.candidate_providers[0]
        print "Candidate provider(s) is (are) %s" % self.candidate_providers
        if self.provider != 'nectar' or len(self.candidate_providers) > 1:
            print "But we use 'nectar' for now..."
            self.provider = 'nectar'

        local_filesystem = 'default'
        data_object = DataObject("runinfo.sys")
        data_object.create(json.dumps({'PROVIDER': self.provider}))
        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)
        return context


class Create(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''
        self.provider = None

    def triggered(self, context):
        """
            Return True if there is a file system and a filesystem and there is a provider
            but now group_id
        """
        self.settings = get_settings(context)
        self.run_info = get_run_info(context)

        if self.settings and self.run_info:
            if 'PROVIDER' in self.run_info:
                self.provider = self.run_info['PROVIDER']
                if 'group_id' in self.run_info:
                    return False
                self.settings.update(self.run_info)  # merge all settings

                return True
        return False

    def process(self, context):
        """
        Make new VMS and store group_id
        """
        number_vm_instances = context['number_vm_instances']
        self.seed = context['seed']
        self.group_id = create_environ(number_vm_instances, self.settings)
        if not self.group_id:
            print "No new VM instance can be created for this computation. Retry later."
            clear_temp_files(context)
            sys.exit()

    def output(self, context):
        """
        Create a runfinos.sys file in filesystem with new group_id
        """
        local_filesystem = 'default'
        data_object = DataObject("runinfo.sys")
        data_object.create(json.dumps({'group_id': self.group_id,
                                       'seed': self.seed,
                                       'PROVIDER': self.provider}))
        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)
        return context


class Run(Stage):
    """
    Start applicaiton on nodes and return status
    """
    def __init__(self):
        self.numbfile = 0

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.
        # input_dir is assumed to be populated.
        '''
        TODO: - uncomment during transformation is in progress
              - change context to self.settings
              - move the code after self.settings.update

               self.input_dir = "input"
        '''

        print "Run stage triggered"
        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.input_dir = "input_%s" % self.id
        else:
            self.input_dir = "input"

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'setup_finished' in self.settings:
            setup_nodes = self.settings['setup_finished']
            logger.debug("setup_nodes = %s" % setup_nodes)
            packaged_nodes = len(botocloudconnector.get_rego_nodes(self.group_id, self.settings))
            logger.debug("packaged_nodes = %s" % packaged_nodes)

            if 'runs_left' in self.settings:
                logger.debug("found runs_left")
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
        """
        Move the input files to the VM
        """
        ip = botocloudconnector.get_instance_ip(instance_id, self.settings)
        ssh = open_connection(ip_address=ip, settings=self.settings)

        # get all files from the payload directory
        dest_files = find_remote_files(ssh, os.path.join(self.settings['DEST_PATH_PREFIX'],
            self.settings['PAYLOAD_CLOUD_DIRNAME']))
        logger.debug("dest_files=%s" % dest_files)

        # keep results of setup stages
        for f in [self.settings['COMPILE_FILE'], "..", "."]:
            try:
                dest_files.remove(os.path.join(self.settings['DEST_PATH_PREFIX'],
                    self.settings['PAYLOAD_CLOUD_DIRNAME'], f))
            except ValueError:
                logger.info("no %s found to remove" % f)

        logger.debug("dest_files=%s" % dest_files)
        # and delete all the rest
        for f in dest_files:
            run_command(ssh, "/bin/rm -f %s" % f)

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
        run_command(ssh, "cd %s; sed -i 's/[0-9]*[ \t]*numbfile.*$/%s\tnumbfile/' rmcen.inp" %
                    (os.path.join(self.settings['DEST_PATH_PREFIX'],
                                  self.settings['PAYLOAD_CLOUD_DIRNAME']), self.numbfile))
        self.numbfile += 1

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

        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
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

        # Get starting value for numbfile from new input file
        # each deployed rmcen.inp has numbfile relative to this.
        rmcen = fsys.retrieve_new(self.input_dir, "rmcen.inp")
        text = rmcen.retrieve()
        p = re.compile("^([0-9]*)[ \t]*numbfile.*$", re.MULTILINE)
        m = p.search(text)
        if m:
            self.numbfile = int(m.group(1))
        else:
            logger.error("could not find numbfile in rmcen.inp")
            self.numbfile = 100  # should not collide with other previous iterations.

        # copy up the new input files to VMs
        for node in nodes:
            instance_id = node.id
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

        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
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
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.output_dir = "output_%s" % self.id
        else:
            self.output_dir = "output"

        # if we have no runs_left then we must have finished all the runs
        if 'runs_left' in self.settings:
            return self.settings['runs_left']
        return False

    def process(self, context):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        self.nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)

        self.error_nodes = []
        self.finished_nodes = []
        for node in self.nodes:
            instance_id = node.id
            ip = botocloudconnector.get_instance_ip(instance_id, self.settings)
            ssh = open_connection(ip_address=ip, settings=self.settings)
            if not botocloudconnector.is_instance_running(instance_id, self.settings):
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
                if not (node.id in [x.id for x in self.finished_nodes]):
                    fsys.download_output(ssh, instance_id, self.output_dir, self.settings)
                else:
                    logger.info("We have already "
                        + "processed output from node %s" % node.id)
                self.finished_nodes.append(node)
            else:
                print "job still running on %s: %s\
                " % (instance_id,
                     botocloudconnector.get_instance_ip(instance_id, self.settings))

    def output(self, context):
        """
        Output new runs_left value (including zero value)
        """
        nodes_working = len(self.nodes) - len(self.finished_nodes)
        update_key('runs_left', nodes_working, context)
        # FIXME: possible race condition?
        update_key('error_nodes', len(self.error_nodes), context)
        update_key('runs_left', nodes_working, context)

        # NOTE: runs_left cannot be deleted or run() will trigger
        return context


# class Converge(Stage):
#     """
#     Determine whether the function has been optimised
#     """
#     # TODO: Might be clearer to count up rather than down as id goes up

#     def __init__(self, number_of_iterations):
#         self.total_iterations = number_of_iterations
#         self.number_of_remaining_iterations = number_of_iterations
#         self.id = 0

#     def triggered(self, context):
#         self.settings = get_run_settings(context)
#         logger.debug("settings = %s" % self.settings)

#         self.settings = get_run_settings(context)
#         logger.debug("settings = %s" % self.settings)

#         self.id = self.settings['id']
#         logger.debug("id = %s" % self.id)

#         if 'transformed' in self.settings:
#             self.transformed = self.settings["transformed"]
#             if self.transformed:
#                 return True
#         return False

#     def process(self, context):
#         self.number_of_remaining_iterations -= 1
#         print "Number of Iterations Left %d\
#         " % self.number_of_remaining_iterations

#         fsys = get_filesys(context)
#         logger.debug("fsys= %s" % fsys)

#         run_info_file = get_file(fsys, "default/runinfo.sys")
#         logger.debug("run_info_file= %s" % run_info_file)

#         settings_text = run_info_file.retrieve()
#         logger.debug("runinfo_text= %s" % settings_text)

#         config = json.loads(settings_text)

#         if self.number_of_remaining_iterations >= 0:
#             del(config['runs_left'])
#             del(config['error_nodes'])  # ??
#             run_info_text = json.dumps(config)
#             run_info_file.setContent(run_info_text)
#             logger.debug("run_info_file=%s" % run_info_file)
#             fsys.update("default", run_info_file)

#     def output(self, context):
#         update_key('converged', False, context)
#         if self.number_of_remaining_iterations == 0:
#             update_key('converged', True, context)
#         delete_key('transformed', context)
#         self.id += 1
#         update_key('id', self.id, context)

#         return context






class Teardown(Stage):
    def triggered(self, context):
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        if 'converged' in self.settings:
            if self.settings['converged']:
                if not 'run_finished' in self.settings:
                    return True
        return False

    def process(self, context):
        all_instances = collect_instances(self.settings,
                                          group_id=self.group_id)
        destroy_environ(self.settings, all_instances)

    def output(self, context):
        update_key('run_finished', True, context)
        return context


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
        context['sleep_done'] = True
        return context
