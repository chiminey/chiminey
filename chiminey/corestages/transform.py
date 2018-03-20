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
import ast
import logging
import datetime

from chiminey.storage import get_url_with_credentials
from chiminey.corestages.stage import Stage
from chiminey.smartconnectorscheduler import jobs
from chiminey.platform import manage
from chiminey import storage
from chiminey.runsettings import getval, setvals, SettingNotFoundException
from chiminey import messages
from django.core.exceptions import ImproperlyConfigured

from chiminey.corestages import timings

logger = logging.getLogger(__name__)

from django.conf import settings as django_settings



class Transform(Stage):
    """
        Convert output into input for next iteration.
    """
    # FIXME: put part of config file, or pull from original input file

    def __init__(self, user_settings=None):

        logger.debug("creating transform")
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        pass

    def is_triggered(self, run_settings):
        try:
            reschedule_str = getval(
                run_settings,
                '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX)
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
            logger.debug('self.procs_2b_rescheduled=%s' % self.procs_2b_rescheduled)
            if self.procs_2b_rescheduled:
                return False
        except SettingNotFoundException, e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX))
            executed_not_running = [x for x in current_processes if x['status'] == 'ready']
            if executed_not_running:
                logger.debug('executed_not_running=%s' % executed_not_running)
                return False
            else:
                logger.debug('No ready: executed_not_running=%s' % executed_not_running)
        except SettingNotFoundException as e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            failed_str = getval(run_settings, '%s/stages/create/failed_nodes' % django_settings.SCHEMA_PREFIX)
            failed_nodes = ast.literal_eval(failed_str)
            created_str = getval(run_settings, '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX)
            created_nodes = ast.literal_eval(created_str)
            if len(failed_nodes) == len(created_nodes) or len(created_nodes) == 0:
                return False
        except SettingNotFoundException as e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            self.converged = int(getval(run_settings, '%s/stages/converge/converged' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError) as e:
            self.converged = 0

        try:
            self.runs_left = getval(run_settings, '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException as e:
            pass
        else:
            try:
                self.transformed = int(getval(run_settings, '%s/stages/transform/transformed' % django_settings.SCHEMA_PREFIX))
            except (SettingNotFoundException, ValueError) as e:
                self.transformed = 0
            if (self.runs_left == 0) and (not self.transformed) and (not self.converged):

                self.wait_stage_end_time = timings.datetime_now_seconds()
                self.wait_stage_start_time = str(getval(run_settings, '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX))
                self.wait_stage_total_time = timings.timedelta_seconds(self.wait_stage_end_time, self.wait_stage_start_time)

                #current_processes_file = str(getval(run_settings, '%s/stages/schedule/current_processes_file' % django_settings.SCHEMA_PREFIX))
                #current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX))
                #timings.update_timings_dump(current_processes_file, current_processes)
                #all_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX))
                #all_processes_file = str(getval(run_settings, '%s/stages/schedule/all_processes_file' % django_settings.SCHEMA_PREFIX))
                #timings.update_timings_dump(all_processes_file, all_processes)
                #timings.analyse_timings_data(run_settings)

                return True
            else:
                logger.debug("%s %s %s" % (self.runs_left, self.transformed, self.converged))
                pass

        return False

    def process(self, run_settings):

        try:
            self.transform_stage_start_time = str(getval(run_settings, '%s/stages/transform/transform_stage_start_time' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.transform_stage_start_time = timings.datetime_now_seconds()
        except ValueError, e:
            logger.error(e)

        try:
            id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            id = 0
        messages.info(run_settings, '%d: transforming' % (id+1))

        # self.contextid = getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)
        bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % django_settings.SCHEMA_PREFIX)

        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % django_settings.SCHEMA_PREFIX)
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        logger.debug("output_storage_settings=%s" % output_storage_settings)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        offset = getval(run_settings, '%s/platform/storage/output/offset' % django_settings.SCHEMA_PREFIX)
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)

        try:
            self.id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output_%s" % self.id))
            self.input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % self.id))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % (self.id + 1)))
        except (SettingNotFoundException, ValueError):
            # FIXME: Not clear that this a valid path through stages
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output"))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "input"))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_1"))

        logger.debug('self.output_dir=%s' % self.output_dir)

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        output_url = get_url_with_credentials(
            output_storage_settings,
            output_prefix + self.output_dir, is_relative_path=False)

        # (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        # fsys = storage.get_filesystem(output_url)

        # node_output_dirs, _ = fsys.listdir(mypath)
        # logger.debug("node_output_dirs=%s" % node_output_dirs)

        outputs = self.process_outputs(run_settings, self.job_dir, output_url, output_storage_settings, offset)
        try:
            curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            curate_data = 0
        if curate_data:

            mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % django_settings.SCHEMA_PREFIX)
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

            all_settings = dict(mytardis_settings)
            all_settings.update(output_storage_settings)
            all_settings['contextid'] = getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)



            try:
                mytardis_platform = jobs.safe_import('chiminey.platform.mytardis.MyTardisPlatform', [], {})
                logger.debug('self_outpus=%s' % outputs)
                self.experiment_id = mytardis_platform.create_dataset_for_intermediate_output(run_settings, self.experiment_id, self.job_dir, output_url, all_settings, outputs=outputs)
            except ImproperlyConfigured as  e:
                logger.error("Cannot load mytardis platform hook %s" % e)

        else:
            logger.warn('Data curation is off')
        
        try:
            self.transform_stage_end_time = str(getval(run_settings, '%s/stages/transform/transform_stage_end_time' % django_settings.SCHEMA_PREFIX))
            logger.debug("WWWWW transform stage end time : %s " % (self.transform_stage_end_time))
        except SettingNotFoundException:
            self.transform_stage_end_time = timings.datetime_now_seconds()
            logger.debug("WWWWW transform stage end time new : %s " % (self.transform_stage_end_time))
        except ValueError, e:
            logger.error(e)


    def output(self, run_settings):
        logger.debug("transform.output")

        transform_stage_total_time = timings.timedelta_seconds(self.transform_stage_end_time, self.transform_stage_end_time) 

        #wait_stage_start_time = str(getval(run_settings, '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX))
        #wait_stage_total_time = timings.timedelta_seconds(wait_stage_end_time, wait_stage_start_time)
        #current_processes_file = str(getval(run_settings, '%s/stages/schedule/current_processes_file' % django_settings.SCHEMA_PREFIX))
        #current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX))
        #timings.update_timings_dump(current_processes_file, current_processes)
        #all_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX))
        #all_processes_file = str(getval(run_settings, '%s/stages/schedule/all_processes_file' % django_settings.SCHEMA_PREFIX))
        #timings.update_timings_dump(all_processes_file, all_processes)

        setvals(run_settings, {
                '%s/stages/transform/transformed' % django_settings.SCHEMA_PREFIX: 1,
                '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX: str(self.experiment_id),
                '%s/stages/transform/transform_stage_start_time' % django_settings.SCHEMA_PREFIX: self.transform_stage_start_time,
                '%s/stages/transform/transform_stage_end_time' % django_settings.SCHEMA_PREFIX: self.transform_stage_end_time,
                '%s/stages/transform/transform_stage_total_time' % django_settings.SCHEMA_PREFIX: transform_stage_total_time,
                '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_start_time,
                '%s/stages/wait/wait_stage_end_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_end_time,
                '%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX: self.wait_stage_total_time,
                })
        #print "End of Transformation: \n %s" % self.audit

        return run_settings

    def process_outputs(self, run_settings, base_dir, output_url, output_storage_settings, offset):
        return
