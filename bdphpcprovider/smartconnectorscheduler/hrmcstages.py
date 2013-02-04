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


from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, collect_instances, destroy_environ





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
    print("config= %s" % config)
    settings_text = config.retrieve()
    print("settings_text= %s" % settings_text)
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
    Returns the content of the run info as file a dict. If problem, return None
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

#
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


        #training_datafile = os.path.join(os.path.dirname(__file__),'provider_training.dat').replace('\\','/')


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
