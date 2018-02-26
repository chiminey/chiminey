
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
from django.core.exceptions import ImproperlyConfigured
from chiminey.smartconnectorscheduler import jobs
logger = logging.getLogger(__name__)


from django.conf import settings as django_settings


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
                                   '%s/stages/transform/transformed' % django_settings.SCHEMA_PREFIX))
            return transformed
        except (SettingNotFoundException, ValueError):
            pass

        return False

    def process(self, run_settings):

        try:
            self.converge_stage_start_time = str(getval(run_settings, '%s/stages/converge/converge_stage_start_time' % django_settings.SCHEMA_PREFIX))
            logger.debug("WWWWW converge stage start time : %s " % (self.converge_stage_start_time))
        except SettingNotFoundException:
            self.converge_stage_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("WWWWW converge stage start time new : %s " % (self.converge_stage_start_time))
        except ValueError, e:
            logger.error(e)


        try:
            id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            id = 0
        messages.info(run_settings, '%d: converging' % (id+1))

        def retrieve_local_settings(run_settings, local_settings):

            update(local_settings, run_settings
                    # '%s/stages/setup/payload_source' % django_settings.SCHEMA_PREFIX,
                    # '%s/stages/setup/payload_destination' % django_settings.SCHEMA_PREFIX,
                    # '%s/system/platform' % django_settings.SCHEMA_PREFIX,
                    # # '%s/stages/create/custom_prompt' % django_settings.SCHEMA_PREFIX,
                    # # '%s/stages/create/cloud_sleep_interval' % django_settings.SCHEMA_PREFIX,
                    # # '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX,
                    # '%s/system/max_seed_int' % django_settings.SCHEMA_PREFIX,
                    # '%s/input/system/cloud/number_vm_instances' % django_settings.SCHEMA_PREFIX,
                    # '%s/input/hrmc/iseed' % django_settings.SCHEMA_PREFIX,
                    # '%s/input/hrmc/optimisation_scheme' % django_settings.SCHEMA_PREFIX,
                    # '%s/input/hrmc/threshold' % django_settings.SCHEMA_PREFIX,
            )
            local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % django_settings.SCHEMA_PREFIX)

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        retrieve_local_settings(run_settings, local_settings)

        bdp_username = local_settings['bdp_username']

        # get output
        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % django_settings.SCHEMA_PREFIX)
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                      output_storage_settings['type'])
        offset = getval(run_settings, '%s/platform/storage/output/offset' % django_settings.SCHEMA_PREFIX)
        job_dir = manage.get_job_dir(output_storage_settings, offset)

        # get mytardis
        #mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % django_settings.SCHEMA_PREFIX)
        #mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

        # setup new paths
        try:
            self.id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
            self.output_dir = os.path.join(job_dir, "output_%d" % self.id)
            self.iter_inputdir = os.path.join(job_dir, "input_%d" % (self.id + 1))
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        except (SettingNotFoundException, ValueError):
            self.output_dir = os.path.join(job_dir, "output")
            self.iter_inputdir = os.path.join(job_dir, "input")
            self.id = 0

        logger.debug('output_dir=%s iter_inputdir=%s' % (self.output_dir, self.iter_inputdir))

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX))
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
                curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % django_settings.SCHEMA_PREFIX)
            except SettingNotFoundException:
                curate_data = 0
            if curate_data:

                mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % django_settings.SCHEMA_PREFIX)
                mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

                all_settings = dict(mytardis_settings)
                all_settings.update(output_storage_settings)

                logger.debug("source_url=%s" % source_url)
                logger.debug("dest_url=%s" % dest_url)
                logger.debug("job_dir=%s" % job_dir)



                try:
                    mytardis_platform = jobs.safe_import('chiminey.platform.mytardis.MyTardisPlatform', [], {})
                    self.experiment_id = mytardis_platform.create_dataset_for_final_output(run_settings, self.experiment_id,job_dir, dest_url, all_settings)
                except ImproperlyConfigured as  e:
                    logger.error("Cannot load mytardis platform hook %s" % e)

            else:
                logger.warn('Data curation is off')

            #messages.info(run_settings, "%s: converged" % (self.id + 1))
        try:
            self.converge_stage_end_time = str(getval(run_settings, '%s/stages/converge/converge_stage_end_time' % django_settings.SCHEMA_PREFIX))
            logger.debug("WWWWW converge stage end time : %s " % (self.converge_stage_end_time))
        except SettingNotFoundException:
            self.converge_stage_end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("WWWWW converge stage end time new : %s " % (self.converge_stage_end_time))
        except ValueError, e:
            logger.error(e)



    def output(self, run_settings):

        convstg_start_time=datetime.datetime.strptime(self.converge_stage_start_time,"%Y-%m-%d  %H:%M:%S")
        convstg_end_time=datetime.datetime.strptime(self.converge_stage_end_time,"%Y-%m-%d  %H:%M:%S")
        total_convstg_time=convstg_end_time - convstg_start_time
        total_time_converge_stage = str(total_convstg_time)

        setval(run_settings, '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX, str(self.experiment_id))

        if not self.done_iterating:
            # trigger first of iteration corestages
            logger.debug("nonconvergence")

            setvals(run_settings, {
                    '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX: '[]',
                    '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX: '[]',
                    '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX: '[]',
                    '%s/stages/schedule/total_scheduled_procs' % django_settings.SCHEMA_PREFIX: 0,
                    '%s/stages/schedule/schedule_completed' % django_settings.SCHEMA_PREFIX: 0,
                    '%s/stages/schedule/schedule_started' % django_settings.SCHEMA_PREFIX: 0
                    })

            logger.debug('scheduled_nodes=%s' % getval(run_settings, '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX))

            try:
                delkey(run_settings, '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX)
            except SettingNotFoundException:
                pass

            try:
                delkey(run_settings, '%s/stages/run/error_nodes' % django_settings.SCHEMA_PREFIX)
            except SettingNotFoundException:
                pass
            # run = run_settings['%s/stages/run' % django_settings.SCHEMA_PREFIX]
            # del run['error_nodes']

            #update_key('converged', False, context)
            setval(run_settings, '%s/stages/converge/converged' % django_settings.SCHEMA_PREFIX, 0)
            # run_settings['%s/stages/converge' % django_settings.SCHEMA_PREFIX][u'converged'] = 0
            # delete_key('runs_left', context)
            # delete_key('error_nodes', context)
            # update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            #update_key('converged', True, context)
            #setval(run_settings, '%s/stages/converge/converged' % django_settings.SCHEMA_PREFIX, 1)
            setvals(run_settings, {
                    '%s/stages/converge/converged' % django_settings.SCHEMA_PREFIX: 1,
                    '%s/stages/converge/converge_stage_start_time' % django_settings.SCHEMA_PREFIX: self.converge_stage_start_time,
                    '%s/stages/converge/converge_stage_end_time' % django_settings.SCHEMA_PREFIX: self.converge_stage_end_time,
                    '%s/stages/converge/total_time_converge_stage' % django_settings.SCHEMA_PREFIX: total_time_converge_stage,
                    })
            # we are done, so don't trigger iteration stages

        #update_key('criterion', self.criterion, context)
        setval(run_settings, '%s/stages/converge/criterion' % django_settings.SCHEMA_PREFIX, unicode(self.criterion))
        # delete_key('error_nodes', context)
        #delete_key('transformed', context)
        try:
            delkey(run_settings, '%s/stages/transform/transformed' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            pass


        self.id += 1
        # update_key('id', self.id, context)

        setval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX, self.id)
        return run_settings

    def process_outputs(self, run_settings, base_dir, output_url, all_settings):
        logger.debug("default process_outputs")

        return (True, '')

    #def curate_dataset(self, run_settings, experiment_id, base_dir,
    #                   output_url, all_settings):

    #    logger.debug("default curate_dataset")

    #    return experiment_id
