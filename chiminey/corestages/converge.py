
# Copyright (C) 2014, RMIT University

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

import os
import logging
from chiminey.storage import get_url_with_credentials

from chiminey.corestages.stage import Stage

from chiminey.smartconnectorscheduler import models
from chiminey import storage

from chiminey.platform import manage
from chiminey import messages
from chiminey.runsettings import getval, delkey, setvals, setval, getvals, update, SettingNotFoundException


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


# TODO: key task here is to seperate the domain specific  parts from the
# general parts of this stage and move to different class/module


class Converge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, user_settings=None):
        """
        """
        logger.debug("created converge")
        self.id = 0

    def is_triggered(self, run_settings):
        """
        """

        try:
            transformed = int(getval(run_settings,
                                   '%s/stages/transform/transformed' % RMIT_SCHEMA))
            return transformed
        except (SettingNotFoundException, ValueError):
            pass

        return False

    def process(self, run_settings):
        try:
            id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            id = 0
        #messages.info(run_settings, '%d: converging' % (id+1))

        def retrieve_local_settings(run_settings, local_settings):

            update(local_settings, run_settings
                    # '%s/stages/setup/payload_source' % RMIT_SCHEMA,
                    # '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
                    # '%s/system/platform' % RMIT_SCHEMA,
                    # # '%s/stages/create/custom_prompt' % RMIT_SCHEMA,
                    # # '%s/stages/create/cloud_sleep_interval' % RMIT_SCHEMA,
                    # # '%s/stages/create/created_nodes' % RMIT_SCHEMA,
                    # '%s/system/max_seed_int' % RMIT_SCHEMA,
                    # '%s/input/system/cloud/number_vm_instances' % RMIT_SCHEMA,
                    # '%s/input/hrmc/iseed' % RMIT_SCHEMA,
                    # '%s/input/hrmc/optimisation_scheme' % RMIT_SCHEMA,
                    # '%s/input/hrmc/threshold' % RMIT_SCHEMA,
            )
            local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        retrieve_local_settings(run_settings, local_settings)

        bdp_username = local_settings['bdp_username']

        # get output
        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                      output_storage_settings['type'])
        offset = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
        job_dir = manage.get_job_dir(output_storage_settings, offset)

        # get mytardis
        #mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
        #mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

        # setup new paths
        try:
            self.id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
            self.output_dir = os.path.join(job_dir, "output_%d" % self.id)
            self.iter_inputdir = os.path.join(job_dir, "input_%d" % (self.id + 1))
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        except (SettingNotFoundException, ValueError):
            self.output_dir = os.path.join(job_dir, "output")
            self.iter_inputdir = os.path.join(job_dir, "input")
            self.id = 0

        logger.debug('output_dir=%s iter_inputdir=%s' % (self.output_dir, self.iter_inputdir))

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        inputdir_url = get_url_with_credentials(output_storage_settings,
            output_prefix + self.iter_inputdir, is_relative_path=False)
        logger.debug('input_dir_url=%s' % inputdir_url)

        # (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(inputdir_url)
        # fsys = storage.get_filesystem(inputdir_url)
        # logger.debug('mypath=%s' % mypath)
        # input_dirs, _ = fsys.listdir(mypath)
        # logger.debug('input_dirs=%s' % input_dirs)

        (self.done_iterating, self.criterion) = self.process_outputs(run_settings, job_dir, inputdir_url, output_storage_settings)

        if self.done_iterating:
            logger.debug("Total Iterations: %d" % self.id)

            # output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
            #                             output_storage_settings['type'])
            # new_output_dir = os.path.join(base_dir, 'output')

            output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])

            # get source url
            iter_output_dir = os.path.join(os.path.join(job_dir, "output_%s" % self.id))

            source_url = "%s%s" % (output_prefix, iter_output_dir)
            # get dest url
            new_output_dir = os.path.join(job_dir, 'output')
            dest_url = "%s%s" % (output_prefix, new_output_dir)

            source_url = get_url_with_credentials(output_storage_settings,
                output_prefix + os.path.join(iter_output_dir), is_relative_path=False)
            dest_url = get_url_with_credentials(output_storage_settings,
                output_prefix + os.path.join(new_output_dir), is_relative_path=False)

            storage.copy_directories(source_url, dest_url)

            # curate
            try:
                curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
            except SettingNotFoundException:
                curate_data = 0
            if curate_data:

                mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
                mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

                all_settings = dict(mytardis_settings)
                all_settings.update(output_storage_settings)

                logger.debug("source_url=%s" % source_url)
                logger.debug("dest_url=%s" % dest_url)
                logger.debug("job_dir=%s" % job_dir)
                self.experiment_id = self.curate_dataset(run_settings, self.experiment_id,
                                                         job_dir, dest_url,
                                                         all_settings)
            else:
                logger.warn('Data curation is off')

            #messages.info(run_settings, "%s: converged" % (self.id + 1))


        # # TODO: store all audit info in single file in input_X directory in transform,
        # # so we do not have to load individual files within node directories here.
        # min_crit = sys.float_info.max - 1.0
        # min_crit_index = sys.maxint

        # # # TODO: store all audit info in single file in input_X directory in transform,
        # # # so we do not have to load individual files within node directories here.
        # # min_crit = sys.float_info.max - 1.0
        # # min_crit_index = sys.maxint
        # logger.debug("input_dirs=%s" % input_dirs)
        # for input_dir in input_dirs:
        #     # Retrieve audit file

        #     audit_url = get_url_with_credentials(output_storage_settings,
        #         output_prefix + os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=False)
        #     audit_content = storage.get_file(audit_url)
        #     logger.debug('audit_url=%s' % audit_url)
        #     # extract the best criterion error
        #     # FIXME: audit.txt is potentially debug file so format may not be fixed.
        #     p = re.compile("Run (\d+) preserved \(error[ \t]*([0-9\.]+)\)", re.MULTILINE)
        #     m = p.search(audit_content)
        #     criterion = None
        #     if m:
        #         criterion = float(m.group(2))
        #         best_numb = int(m.group(1))
        #         # NB: assumes that subdirss in new input_x will have same names as output dir that created it.
        #         best_node = input_dir
        #     else:
        #         message = "Cannot extract criterion from audit file for iteration %s" % (self.id + 1)
        #         logger.warn(message)
        #         raise IOError(message)

        #     if criterion < min_crit:
        #         min_crit = criterion
        #         min_crit_index = best_numb
        #         min_crit_node = best_node

        # logger.debug("min_crit = %s at %s" % (min_crit, min_crit_index))

        # if min_crit_index >= sys.maxint:
        #     raise BadInputException("Unable to find minimum criterion of input files")

        # # get previous best criterion

        # try:
        #     self.prev_criterion = float(getval(run_settings, '%s/converge/criterion' % RMIT_SCHEMA))
        # except (SettingNotFoundException, ValueError):
        #     self.prev_criterion = sys.float_info.max - 1.0
        #     logger.warn("no previous criterion found")
        # # if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge', u'criterion'):
        # #     self.prev_criterion = float(run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'])
        # # else:
        # #     self.prev_criterion = sys.float_info.max - 1.0
        # #     logger.warn("no previous criterion found")

        # # check whether we are under the error threshold
        # logger.debug("best_num=%s" % best_numb)
        # logger.debug("prev_criterion = %f" % self.prev_criterion)
        # logger.debug("min_crit = %f" % min_crit)
        # self.done_iterating = False

        # difference = self.prev_criterion - min_crit
        # logger.debug("Difference %f" % difference)

        # try:
        #     max_iteration = int(getval(run_settings, '%s/input/hrmc/max_iteration' % RMIT_SCHEMA))
        # except (ValueError, SettingNotFoundException):
        #     raise BadInputException("unknown max_iteration")
        # # if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/hrmc', u'max_iteration'):
        # #     max_iteration = int(run_settings['http://rmit.edu.au/schemas/input/hrmc'][u'max_iteration'])
        # # else:
        # #     raise BadInputException("unknown max_iteration")
        # logger.debug("max_iteration=%s" % max_iteration)

        # if self.id >= (max_iteration - 1):
        #     logger.debug("Max Iteration Reached %d " % self.id)
        #     self.done_iterating = True

        # elif min_crit <= self.prev_criterion and difference <= self.error_threshold:
        #     self.done_iterating = True
        #     logger.debug("Convergence reached %f" % difference)

        # else:
        #     if difference < 0:
        #         logger.debug("iteration diverged")
        #     logger.debug("iteration continues: %d iteration so far" % self.id)

        # if self.done_iterating:
        #     logger.debug("Total Iterations: %d" % self.id)
        #     self._ready_final_output(min_crit_node, min_crit_index, output_storage_settings, mytardis_settings, run_settings)
        #     messages.success(run_settings, "%s: finished" % (self.id + 1))
        # logger.debug('Current min criterion: %f, Prev '
        #              'criterion: %f' % (min_crit, self.prev_criterion))

        # self.criterion = min_crit

    def output(self, run_settings):

        # if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge'):
        #     run_settings['http://rmit.edu.au/schemas/stages/converge'] = {}

        setval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA, str(self.experiment_id))
        # run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] = str(self.experiment_id)

        if not self.done_iterating:
            # trigger first of iteration corestages
            logger.debug("nonconvergence")

            setvals(run_settings, {
                    '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA: '[]',
                    '%s/stages/execute/executed_procs' % RMIT_SCHEMA: '[]',
                    '%s/stages/schedule/current_processes' % RMIT_SCHEMA: '[]',
                    '%s/stages/schedule/total_scheduled_procs' % RMIT_SCHEMA: 0,
                    '%s/stages/schedule/schedule_completed' % RMIT_SCHEMA: 0,
                    '%s/stages/schedule/schedule_started' % RMIT_SCHEMA: 0
                    })
            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #          {})[u'scheduled_nodes'] = '[]'

            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/execute',
            #      {})[u'executed_procs'] = '[]'

            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #     {})[u'current_processes'] = '[]'

            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #     {})[u'total_scheduled_procs'] = 0

            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #     {})[u'schedule_completed'] = 0

            # run_settings.setdefault(
            #     'http://rmit.edu.au/schemas/stages/schedule',
            #     {})[u'schedule_started'] = 0

            logger.debug('scheduled_nodes=%s' % getval(run_settings, '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA))

            try:
                delkey(run_settings, '%s/stages/run/runs_left' % RMIT_SCHEMA)
            except SettingNotFoundException:
                pass
            # run = run_settings['http://rmit.edu.au/schemas/stages/run']
            # del run['runs_left']

            try:
                delkey(run_settings, '%s/stages/run/error_nodes' % RMIT_SCHEMA)
            except SettingNotFoundException:
                pass
            # run = run_settings['%s/stages/run' % RMIT_SCHEMA]
            # del run['error_nodes']

            #update_key('converged', False, context)
            setval(run_settings, '%s/stages/converge/converged' % RMIT_SCHEMA, 0)
            # run_settings['%s/stages/converge' % RMIT_SCHEMA][u'converged'] = 0
            # delete_key('runs_left', context)
            # delete_key('error_nodes', context)
            # update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            #update_key('converged', True, context)
            setval(run_settings, '%s/stages/converge/converged' % RMIT_SCHEMA, 1)
            # run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'] = 1
            # we are done, so don't trigger iteration stages

        #update_key('criterion', self.criterion, context)
        setval(run_settings, '%s/stages/converge/criterion' % RMIT_SCHEMA, unicode(self.criterion))
        # run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'] = unicode(self.criterion)
         # delete_key('error_nodes', context)
        #delete_key('transformed', context)
        try:
            delkey(run_settings, '%s/stages/transform/transformed' % RMIT_SCHEMA)
        except SettingNotFoundException:
            pass
        # run = run_settings['http://rmit.edu.au/schemas/stages/transform']
        # del run['transformed']

        self.id += 1
        # update_key('id', self.id, context)

        setval(run_settings, '%s/system/id' % RMIT_SCHEMA, self.id)
        # run_settings['http://rmit.edu.au/schemas/system'][u'id'] = self.id
        return run_settings

    def process_outputs(self, run_settings, base_dir, output_url, all_settings):
        logger.debug("default process_outputs")

        return (True, '')

    def curate_dataset(self, run_settings, experiment_id, base_dir,
                       output_url, all_settings):

        logger.debug("default curate_dataset")

        return experiment_id
