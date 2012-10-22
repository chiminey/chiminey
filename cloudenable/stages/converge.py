
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
import logging
import sys
import logging.config

from hrmcstages import get_run_settings
from hrmcstages import update_key
from hrmcstages import get_filesys
from hrmcstages import delete_key

logger = logging.getLogger('stages')

from smartconnector import Stage


class IterationConverge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, number_of_iterations):
        print "hello"
        logger.debug("created iteration converge")
        self.total_iterations = number_of_iterations
        self.number_of_remaining_iterations = number_of_iterations
        self.id = 0

    def triggered(self, context):
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.id = self.settings['id']
        logger.debug("id = %s" % self.id)

        if 'transformed' in self.settings:
            self.transformed = self.settings["transformed"]
            if self.transformed:
                return True
        return False

    def process(self, context):
        self.number_of_remaining_iterations -= 1
        print "Number of Iterations Left %d" \
            % self.number_of_remaining_iterations

    def output(self, context):

        if self.number_of_remaining_iterations > 0:
            # trigger first of iteration stages
            logger.debug("nonconvergence")
            delete_key('runs_left', context)
            delete_key('error_nodes', context)
            update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            update_key('converged', True, context)
            # we are done, so don't trigger iteration stages

        delete_key('transformed', context)
        self.id += 1
        update_key('id', self.id, context)

        return context


class Converge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, error_threshold):
        logger.debug("created converge")
        self.error_threshold = error_threshold
        self.id = 0

    def triggered(self, context):
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)


        if 'id' in self.settings:
            self.id = self.settings['id']
            self.output_dir = "output_%d" % self.id
            self.input_dir = "input_%d" % self.id
            self.new_input_dir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = "output"
            self.output_dir = "input"
            self.new_input_dir = "input_1"

        if 'transformed' in self.settings:
            self.transformed = self.settings["transformed"]
            if self.transformed:
                return True
        return False

    def process(self, context):

        # TODO: should keep track of the criterion from the last iteration
        # to handle the error condition where criterion is diverging
        # TODO: should could number of iterations to indicate if the
        # convergence is very slow.

        # retrive the audit file for last iteration
        fs = get_filesys(context)
        if not fs:
            logger.error("cannot retrieve filesystem")
            raise IOError
        try:
            text = fs.retrieve_new(directory=self.new_input_dir,
                          file="audit.txt").retrieve()
        except IOError:
            logger.warn("no audit found")
            raise
        logger.debug("text=%s" % text)

        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        if 'criterion' in self.settings:
            self.prev_criterion = float(self.settings['criterion'])
        else:
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # extract the best criterion error from last iteration
        p = re.compile("Run (\d+) preserved \(error[ \t]*([0-9\.]+)\)", re.MULTILINE)
        m = p.search(text)
        self.criterion = None
        if m:
            self.criterion = float(m.group(2))
            self.best_num = int(m.group(1))
        else:
            message = "cannot extract criterion from audit file for iteration %s" % (self.id + 1)
            logger.warn(message)
            raise IOError(message)

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % self.best_num)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("criterion = %f" % self.criterion)
        self.done_iterating = False
        if self.criterion > self.prev_criterion:
            logger.error('iteration %s is diverging' % self.best_num)
            self.done_iterating = True  # if we are diverging then end now
        elif (self.prev_criterion - self.criterion) <= self.error_threshold:
            self.done_iterating = True
            self._ready_final_output(fs)
        else:
            logger.debug("iteration continues")

    def _ready_final_output(self, fs):


        new_output_dir = 'output'
        # FIXME: check new_output_dir does not already exist
        fs.create_local_filesystem(new_output_dir)

        for node_dir in fs.get_local_subdirectories(self.output_dir):
            grerr = None
            try:
                grerr = fs.retrieve_under_dir(local_filesystem=self.output_dir,
                                             directory=node_dir,
                                             file="grerr%s.dat" % str(self.best_num).zfill(2)).retrieve()
            except IOError:
                logger.warn("no grerr found")

            if grerr:
                files_to_copy = fs.get_local_subdirectory_files(self.output_dir,
                                             node_dir)
                logger.debug("files_to_copy=%s" % files_to_copy)

                for f in files_to_copy:
                    logger.debug("f=%s" % f)
                    fs.copy(self.output_dir, node_dir, f, new_output_dir, f)
            else:
                logger.debug("skipping %s" % node_dir)


    def output(self, context):

        if not self.done_iterating:
            # trigger first of iteration stages
            logger.debug("nonconvergence")
            delete_key('runs_left', context)
            delete_key('error_nodes', context)
            update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            update_key('converged', True, context)
            # we are done, so don't trigger iteration stages

        update_key('criterion', self.criterion, context)
        delete_key('transformed', context)
        self.id += 1
        update_key('id', self.id, context)

        return context



