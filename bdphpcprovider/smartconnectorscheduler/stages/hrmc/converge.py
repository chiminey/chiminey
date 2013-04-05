
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

import re
import os
import logging
import sys
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException

logger = logging.getLogger(__name__)


class IterationConverge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, user_settings=None):
        """
        """
        logger.debug("created iteration converge")
        self.total_iterations = 30
        self.number_of_remaining_iterations = 30
        self.id = 0
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number


    def triggered(self, run_settings):
        """
        """
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
        else:
            logger.warn("Cannot retrieve id. Maybe first iteration?")
            self.id = 0
        logger.debug("id = %s" % self.id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
            self.transformed = run_settings['http://rmit.edu.au/schemas/stages/transformed'][u'transformed']
            if self.transformed:
                return True
        return False

    def process(self, context):
        """
        """
        self.number_of_remaining_iterations -= 1
        print "Number of Iterations Left %d" \
            % self.number_of_remaining_iterations

    def output(self, run_settings):
        """
        """
        if self.number_of_remaining_iterations > 0:
            # trigger first of iteration stages
            logger.debug("nonconvergence")

            # delete_key('runs_left', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['runs_left']

            # delete_key('error_nodes', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['error_nodes']

            #update_key('converged', False, context)
            run_settings['http://rmit.edu.au/stages/converge']['converged'] = False
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge

            # update_key('converged', True, context)
            run_settings['http://rmit.edu.au/stages/converge']['converged'] = True

            # we are done, so don't trigger iteration stages

        #delete_key('transformed', context)
        transform = run_settings['http://rmit.edu.au/schemas/stages/transform']
        del transform['transformed']

        self.id += 1
        #update_key('id', self.id, context)
        run_settings['http://rmit.edu.au/schemas/system/misc'][u'id'] = self.id

        return run_settings


class Converge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, user_settings=None):
        """
        """
        logger.debug("created converge")
        self.user_settings = user_settings.copy()
        self.boto_settings = user_settings.copy()
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        self.id = 0

    def triggered(self, run_settings):
        """
        """

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.output_dir = os.path.join(self.job_dir, "output_%d" % self.id)
            self.iter_inputdir = os.path.join(self.job_dir, "input_%d" % (self.id + 1))
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = os.path.join(self.job_dir, "output")
            self.iter_inputdir = os.path.join(self.job_dir, "input")
            self.id = 0

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'error_threshold'):
            self.error_threshold = float(run_settings['http://rmit.edu.au/schemas/hrmc'][u'error_threshold'])
        else:
            pass  # FIXME: is this an error condition?

        logger.debug("error_threshold=%s" % self.error_threshold)
        # if 'id' in self.settings:
        #     self.id = self.settings['id']
        #     self.output_dir = "output_%d" % self.id
        #     self.iter_inputdir = "input_%d" % (self.id + 1)
        #     #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        # else:
        #     self.output_dir = "output"
        #     self.iter_inputdir = "input"
        #     self.id = 0

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
            self.transformed = run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed']
            if self.transformed:
                return True

        # if 'transformed' in self.settings:
        #     self.transformed = self.settings["transformed"]
        #     if self.transformed:
        #         return True

        return False

    def process(self, run_settings):

        #import time
        # start_time = time.time()
        # logger.debug("Start time %f "% start_time)


        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/group_id_dir')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/max_seed_int')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/compile_file')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/retry_attempts')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')
        self.boto_settings['private_key'] = self.user_settings['nectar_private_key']
        self.boto_settings['username'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']

        inputdir_url = smartconnector.get_url_with_pkey(self.boto_settings,
            self.iter_inputdir, is_relative_path=True)
        fsys = hrmcstages.get_filesystem(inputdir_url)
        input_dirs, _ = fsys.listdir(self.iter_inputdir)
        # TODO: store all audit info in single file in input_X directory in transform,
        # so we do not have to load individual files within node directories here.
        min_crit = sys.float_info.max - 1.0
        min_crit_index = sys.maxint

        # # retrive the audit file for last iteration
        # fs = get_filesys(context)

        # self.settings = get_all_settings(context)
        # logger.debug("settings = %s" % self.settings)

        # logger.debug("input dir %s" % self.iter_inputdir)
        # input_dirs = fs.get_local_subdirectories(self.iter_inputdir)
        # logger.debug("input_dirs = %s" % input_dirs)

        # # TODO: store all audit info in single file in input_X directory in transform,
        # # so we do not have to load individual files within node directories here.
        # min_crit = sys.float_info.max - 1.0
        # min_crit_index = sys.maxint
        logger.debug("input_dirs=%s" % input_dirs)
        for input_dir in input_dirs:
            # Retrieve audit file

            # if not fs.isdir(self.iter_inputdir, input_dir):
            #     continue
            # try:
            #     text = fs.retrieve_under_dir(self.iter_inputdir, input_dir,
            #         "audit.txt").retrieve()
            # except IOError:
            #     logger.warn("Cannot retrieve audit.txt file from node directory")
            #     raise
            # logger.debug("text=%s" % text)

            audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=True)
            audit_content = hrmcstages.get_file(audit_url)

            # extract the best criterion error
            # FIXME: audit.txt is potentially debug file so format may not be fixed.
            p = re.compile("Run (\d+) preserved \(error[ \t]*([0-9\.]+)\)", re.MULTILINE)
            m = p.search(audit_content)
            criterion = None
            if m:
                criterion = float(m.group(2))
                best_numb = int(m.group(1))
                # NB: assumes that subdirss in new input_x will have same names as output dir that created it.
                best_node = input_dir
            else:
                message = "Cannot extract criterion from audit file for iteration %s" % (self.id + 1)
                logger.warn(message)
                raise IOError(message)

            if criterion < min_crit:
                min_crit = criterion
                min_crit_index = best_numb
                min_crit_node = best_node

        logger.debug("min_crit = %s at %s" % (min_crit, min_crit_index))

        if min_crit_index >= sys.maxint:
            raise BadInputException("Unable to find minimum criterion of input files")

        # get previous best criterion

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge', u'criterion'):
            self.prev_criterion = float(run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'])
        else:
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # if 'criterion' in self.settings:
        #     self.prev_criterion = float(self.settings['criterion'])
        # else:
        #     self.prev_criterion = sys.float_info.max - 1.0
        #     logger.warn("no previous criterion found")

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % best_numb)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("min_crit = %f" % min_crit)
        self.done_iterating = False

        difference = self.prev_criterion - min_crit
        logger.debug("Difference %f" % difference)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'max_iteration'):
            max_iteration = int(run_settings['http://rmit.edu.au/schemas/hrmc'][u'max_iteration'])
        else:
            raise BadInputException("unknown max_iteration")
        logger.debug("max_iteration=%s" % max_iteration)

        if self.id >= max_iteration:
            logger.debug("Max Iteration Reached %d " % self.id)
            self.done_iterating = True

        elif min_crit <= self.prev_criterion and difference <= self.error_threshold:
            self.done_iterating = True
            logger.debug("Convergence reached %f" % difference)

        else:
            if difference < 0:
                logger.debug("iteration diverged")
            logger.debug("iteration continues: %d iteration so far" % self.id)

        if self.done_iterating:
            logger.debug("Total Iterations: %d" % self.id)
            self._ready_final_output(min_crit_node, min_crit_index)

        logger.error('Current min criterion: %f, Prev '
                     'criterion: %f' % (min_crit, self.prev_criterion))

        self.criterion = min_crit

        # # end_time = time.time()
        # # logger.debug("End time %f "% end_time)

        # try:
        #     converge_vec = self.settings['converge_time']
        # except KeyError:
        #     converge_vec = []

        # converge_vec.append(end_time-start_time)
        # update_key("converge_time", converge_vec, self.settings)

    def _ready_final_output(self, crit_node, crit_index):

        new_output_dir = os.path.join(self.job_dir,  'output')
        # FIXME: check new_output_dir does not already exist
        #fs.create_local_filesystem(new_output_dir)

        # import shutil, os.path
        # source = os.path.join(fs.get_global_filesystem(), self.output_dir, crit_node)
        # dest = os.path.join(fs.get_global_filesystem(), new_output_dir)
        # logger.debug("Convergence Source %s Destination %s " % (source, dest))
        # shutil.copytree(source, dest)

        source_url = smartconnector.get_url_with_pkey(self.boto_settings,
            os.path.join(self.output_dir), is_relative_path=True)
        dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
            os.path.join(new_output_dir), is_relative_path=True)

        hrmcstages.copy_directories(source_url, dest_url)

    def output(self, run_settings):

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge'):
            run_settings['http://rmit.edu.au/schemas/stages/converge'] = {}

        if not self.done_iterating:
            # trigger first of iteration stages
            logger.debug("nonconvergence")

            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['runs_left']

            # delete_key('error_nodes', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['error_nodes']

            #update_key('converged', False, context)
            run_settings['http://rmit.edu.au/schemas/stages/converge']['converged'] = False
            # delete_key('runs_left', context)
            # delete_key('error_nodes', context)
            # update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            #update_key('converged', True, context)
            run_settings['http://rmit.edu.au/schemas/stages/converge']['converged'] = True
            # we are done, so don't trigger iteration stages

        #update_key('criterion', self.criterion, context)
        run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'] = unicode(self.criterion)
         # delete_key('error_nodes', context)
        #delete_key('transformed', context)
        run = run_settings['http://rmit.edu.au/schemas/stages/transform']
        del run['transformed']

        self.id += 1
        # update_key('id', self.id, context)
        run_settings['http://rmit.edu.au/schemas/system/misc'][u'id'] = self.id

        return run_settings

