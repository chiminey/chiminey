
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

from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_all_settings, update_key, get_filesys, delete_key

logger = logging.getLogger(__name__)

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage


from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException

class IterationConverge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, number_of_iterations):
        """
        """
        logger.debug("created iteration converge")
        self.total_iterations = number_of_iterations
        self.number_of_remaining_iterations = number_of_iterations
        self.id = 0

    def triggered(self, context):
        """
        """
        self.settings = get_all_settings(context)
        logger.debug("settings = %s" % self.settings)

        try:
            self.id = self.settings['id']
        except KeyError:
            logger.warn("Cannot retrieve id. Maybe first iteration?")
            self.id = 0
        logger.debug("id = %s" % self.id)

        if 'transformed' in self.settings:
            self.transformed = self.settings["transformed"]
            if self.transformed:
                return True
        return False

    def process(self, context):
        """
        """
        self.number_of_remaining_iterations -= 1
        print "Number of Iterations Left %d" \
            % self.number_of_remaining_iterations

    def output(self, context):
        """
        """
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
        """
        """
        logger.debug("created converge")
        self.error_threshold = error_threshold
        self.id = 0

    def triggered(self, context):
        """
        """
        self.settings = get_all_settings(context)
        logger.debug("settings = %s" % self.settings)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.output_dir = "output_%d" % self.id
            self.iter_inputdir = "input_%d" % (self.id + 1)
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = "output"
            self.iter_inputdir = "input"
            self.id = 0

        if 'transformed' in self.settings:
            self.transformed = self.settings["transformed"]
            if self.transformed:
                return True
        return False

    def process(self, context):

        # retrive the audit file for last iteration
        fs = get_filesys(context)

        self.settings = get_all_settings(context)
        logger.debug("settings = %s" % self.settings)

        input_dirs = fs.get_local_subdirectories(self.iter_inputdir)
        logger.debug("input_dirs = %s" % input_dirs)

        # TODO: store all audit info in single file in input_X directory in transform,
        # so we do not have to load individual files within node directories here.
        min_crit = sys.float_info.max - 1.0
        min_crit_index = sys.maxint
        for input_dir in input_dirs:
            # Retrieve audit file
            if not fs:
                logger.error("Cannot retrieve filesystem from context")
                raise IOError("Cannot retrieve filesystem from context")

            if not fs.isdir(self.iter_inputdir, input_dir):
                continue
            try:
                text = fs.retrieve_under_dir(self.iter_inputdir, input_dir,
                    "audit.txt").retrieve()
            except IOError:
                logger.warn("Cannot retrieve audit.txt file from node directory")
                raise
            logger.debug("text=%s" % text)

            # extract the best criterion error
            # FIXME: audit.txt is potentially debug file so format may not be fixed.
            p = re.compile("Run (\d+) preserved \(error[ \t]*([0-9\.]+)\)", re.MULTILINE)
            m = p.search(text)
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
        if 'criterion' in self.settings:
            self.prev_criterion = float(self.settings['criterion'])
        else:
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % best_numb)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("min_crit = %f" % min_crit)
        self.done_iterating = False
        if min_crit > self.prev_criterion:
            logger.error('iteration %s is diverging' % best_numb)
            self.done_iterating = True  # if we are diverging then end now

        elif (self.prev_criterion - min_crit) <= self.error_threshold:
            self.done_iterating = True
            self._ready_final_output(fs, min_crit_node, min_crit_index)
        else:
            logger.debug("iteration continues")
        self.criterion = min_crit

    def _ready_final_output(self, fs, crit_node, crit_index):

        new_output_dir = 'output'
        # FIXME: check new_output_dir does not already exist
        #fs.create_local_filesystem(new_output_dir)

        import shutil, os.path
        source = os.path.join(fs.get_global_filesystem(), self.output_dir, crit_node)
        dest = os.path.join(fs.get_global_filesystem(), new_output_dir)
        logger.debug("Convergence Source %s Destination %s " % (source, dest))
        shutil.copytree(source, dest)

        ''''
        gerr_object = None
        try:
            gerr_object = fs.retrieve_under_dir(local_filesystem=self.output_dir,
                directory=crit_node,
                file="grerr%s.dat" % str(crit_index).zfill(2)).retrieve()
        except IOError:
            logger.warn("No gerrX.dat found at %s/%s" % (self.iter_inputdir, crit_node))

        if gerr_object:
            files_to_copy = fs.get_local_subdirectory_files(self.output_dir, crit_node)
            logger.debug("files_to_copy=%s" % files_to_copy)

            for f in files_to_copy:
                logger.debug("f=%s" % f)
                try:
                    fs.copy(self.output_dir, crit_node, f, new_output_dir, f)
                except IOError:
                    logger.exception("Cannot copy output file %s to final destination %s " % (f, new_output_dir))
            else:
                logger.debug("skipping %s" % f)
        '''

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



