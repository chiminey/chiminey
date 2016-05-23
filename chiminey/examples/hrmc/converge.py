

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

#

import re
import os
import logging
import json
import sys
from chiminey.smartconnectorscheduler.errors import BadInputException
from chiminey.storage import get_url_with_credentials
from chiminey import storage
from chiminey import mytardis
from chiminey.runsettings import getval, SettingNotFoundException
from chiminey.corestages import Converge

from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


RMIT_SCHEMA = django_settings.SCHEMA_PREFIX
DATA_ERRORS_FILE = "data_errors.dat"
STEP_COLUMN_NUM = 0
ERRGR_COLUMN_NUM = 28


class HRMCConverge(Converge):

    SCHEMA_PREFIX = django_settings.SCHEMA_PREFIX
    VALUES_FNAME = "values"

    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem
        """
        error = []
        try:
            int(getval(settings_to_test, '%s/input/hrmc/max_iteration' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            error.append("Cannot load max_iteration")

        try:
            float(getval(settings_to_test, '%s/input/hrmc/error_threshold' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            error.append("Cannot load error threshold")

        if error:
            return (False, '. '.join(error))
        return (True, "ok")


    def process_outputs(self, run_settings, base_dir, input_url, all_settings):

        id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        iter_output_dir = os.path.join(os.path.join(base_dir, "input_%s" % (id + 1)))
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)

        (scheme, host, iter_output_path, location, query_settings) = storage.parse_bdpurl(input_url)
        iter_out_fsys = storage.get_filesystem(input_url)

        input_dirs, _ = iter_out_fsys.listdir(iter_output_path)

        # TODO: store all audit info in single file in input_X directory in transform,
        # so we do not have to load individual files within node directories here.
        min_crit = sys.float_info.max - 1.0
        min_crit_index = sys.maxint

        # # TODO: store all audit info in single file in input_X directory in transform,
        # # so we do not have to load individual files within node directories here.
        # min_crit = sys.float_info.max - 1.0
        # min_crit_index = sys.maxint
        logger.debug("input_dirs=%s" % input_dirs)
        for input_dir in input_dirs:
            node_path = os.path.join(iter_output_dir, input_dir)
            logger.debug('node_path= %s' % node_path)

            # Retrieve audit file

            # audit_url = get_url_with_credentials(output_storage_settings,
            #     output_prefix + os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=False)
            audit_url = get_url_with_credentials(all_settings, os.path.join(node_path, "audit.txt"), is_relative_path=False)
            audit_content = storage.get_file(audit_url)
            logger.debug('audit_url=%s' % audit_url)

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
        try:
            self.prev_criterion = float(getval(run_settings, '%s/converge/criterion' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % best_numb)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("min_crit = %f" % min_crit)
        logger.debug('Current min criterion: %f, Prev '
                     'criterion: %f' % (min_crit, self.prev_criterion))
        difference = self.prev_criterion - min_crit
        logger.debug("Difference %f" % difference)

        try:
            max_iteration = int(getval(run_settings, '%s/input/hrmc/max_iteration' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            raise BadInputException("unknown max_iteration")
        logger.debug("max_iteration=%s" % max_iteration)

        try:
            self.error_threshold = float(getval(run_settings, '%s/input/hrmc/error_threshold' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            raise BadInputException("uknown error threshold")
        logger.debug("error_threshold=%s" % self.error_threshold)

        if self.id >= (max_iteration - 1):
            logger.debug("Max Iteration Reached %d " % self.id)
            return (True, min_crit)

        elif min_crit <= self.prev_criterion and difference <= self.error_threshold:
            logger.debug("Convergence reached %f" % difference)
            return (True, min_crit)

        else:
            if difference < 0:
                logger.debug("iteration diverged")
            logger.debug("iteration continues: %d iteration so far" % self.id)

        return (False, min_crit)
