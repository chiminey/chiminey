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
from pprint import pformat
from chiminey.platform import manage
from chiminey.corestages import stage
from chiminey.platform import *
from chiminey.corestages import timings

from chiminey.corestages.stage import Stage, UI
from chiminey.smartconnectorscheduler import models

from chiminey import mytardis
from chiminey import messages
from chiminey import storage

from chiminey.runsettings import getval, getvals, setval, update, SettingNotFoundException
from chiminey.storage import get_url_with_credentials
from django.core.exceptions import ImproperlyConfigured
from chiminey.smartconnectorscheduler import jobs

logger = logging.getLogger(__name__)


from django.conf import settings as django_settings


class Configure(Stage):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,

    """
    NETWORK_IO_USAGE_LOG = django_settings.NETWORK_IO_USAGE_LOG

    def __init__(self, user_settings=None):
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number

    def is_triggered(self, run_settings):
        try:
            configure_done = int(getval(run_settings,
                '%s/stages/configure/configure_done' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            return True
        except ValueError:
            return True
        else:
            return not configure_done

    def setup_input(self, run_settings):
        self.input_platform_name = ''
        self.input_platform_offset = ''
        if self.input_exists(run_settings):
            try:
                 run_settings['%s/platform/storage/input' % django_settings.SCHEMA_PREFIX]
            except KeyError:
                try:
                    bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/system/input_location')
                except SettingNotFoundException:
		    try:
                   	 bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input_location')
		    except SettingNotFoundException:
			 bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input/input_location')
                self.input_platform_name, self.input_platform_offset = self.break_bdp_url(bdp_url)
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/input'] = {}
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/input'][
                'platform_url'] = self.input_platform_name
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/input']['offset'] = self.input_platform_offset

    def setup_output(self, run_settings):
        self.output_platform_name = ''
        self.output_platform_offset = ''
        self.output_loc_offset = ''
        if self.output_exists(run_settings):
            logger.debug('special=%s' % run_settings)
            try:
                run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]
            except KeyError:
                logger.debug('bdp_url settings ...')
                try:
                    bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/system/output_location')
                    logger.debug('bdp_url=%s' % bdp_url)
                except SettingNotFoundException:
                    try:
                        bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/output_location')
                        logger.debug('bdp_url=%s' % bdp_url)
                    except SettingNotFoundException:
                        bdp_url = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/output/output_location')
                        logger.debug('bdp_url=%s' % bdp_url)
                self.output_platform_name, self.output_platform_offset = self.break_bdp_url(bdp_url)
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/output'] = {}
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/output'][
                    'platform_url'] = self.output_platform_name
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/output']['offset'] = self.output_platform_offset

    def setup_computation(self, run_settings):
        self.compute_platform_name = ''
        self.compute_platform_offset = ''
        try:
             run_settings['%s/platform/computation' % django_settings.SCHEMA_PREFIX]
        except KeyError:
            logger.debug('compplatform=empty')
            compplatform = [k for k, v in run_settings.items()
                            if k.startswith('%s/input/system/compplatform' % django_settings.SCHEMA_PREFIX)]
            logger.debug('compplatform=%s' % compplatform)

            bdp_url =  run_settings[compplatform[0]]['computation_platform']
            logger.debug('tbdp_url=%s' % bdp_url)
            self.compute_platform_name, self.compute_platform_offset = self.break_bdp_url(bdp_url)
            run_settings[django_settings.SCHEMA_PREFIX + '/platform/computation'] = {}
            run_settings[django_settings.SCHEMA_PREFIX + '/platform/computation']['platform_url'] = self.compute_platform_name
            run_settings[django_settings.SCHEMA_PREFIX + '/platform/computation']['offset'] = self.compute_platform_offset

    def setup_scratchspace(self, run_settings, offset="input_0"):

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        logger.debug("settings=%s" % pformat(run_settings))
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % django_settings.SCHEMA_PREFIX)
        # local_settings['bdp_username'] = run_settings[
        #     django_settings.SCHEMA_PREFIX + '/bdp_userprofile']['username']
        logger.debug('local_settings=%s' % local_settings)

        self.contextid = getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)
        logger.debug("self.contextid=%s" % self.contextid)
        self.output_loc_offset = str(self.contextid)


        self.output_loc_offset = self.get_results_dirname(run_settings)
        logger.debug('self.output_loc_offset=%s' % self.output_loc_offset)
        if self.input_exists(run_settings):
            logger.debug('copy to scratch')
            self.copy_to_scratch_space(run_settings, local_settings, offset)
        else:
            logger.debug('not copy to scratch')

    def process(self, run_settings):


        logger.debug('run_settings=%s' % run_settings)
        #create empty network io usage log file
        self.NETWORK_IO_USAGE_LOG = timings.create_input_output_log(str(getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)), self.NETWORK_IO_USAGE_LOG)
        self.setup_output(run_settings)
        self.setup_input(run_settings)
        self.setup_computation(run_settings)

        messages.info(run_settings, "0: Setting up computation")

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        logger.debug("settings=%s" % pformat(run_settings))
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % django_settings.SCHEMA_PREFIX)
        # local_settings['bdp_username'] = run_settings[
        #     django_settings.SCHEMA_PREFIX + '/bdp_userprofile']['username']
        logger.debug('local_settings=%s' % local_settings)


        self.setup_scratchspace(run_settings)

        output_location = self.output_loc_offset  # run_settings[django_settings.SCHEMA_PREFIX + '/input/system'][u'output_location']

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0
        try:
            curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            curate_data = False
        if curate_data:
            try:
                mytardis_platform = jobs.safe_import('chiminey.platform.mytardis.MyTardisPlatform', [], {})
                self.experiment_id = mytardis_platform.create_experiment(run_settings,
                    output_location, self.experiment_id)
            except ImproperlyConfigured as  e:
                logger.error("Cannot load mytardis platform hook %s" % e)


    def writeout_output(self, run_settings):
        if self.output_exists(run_settings):
            if self.output_platform_name:
                run_settings.setdefault(
                    django_settings.SCHEMA_PREFIX + '/platform/storage/output',
                    {})[u'platform_url'] = self.output_platform_name
            #if self.output_platform_offset:
            #    run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/output']['offset'] = self.output_platform_offset
            #else:
            run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset'] = self.output_loc_offset

    def writeout_input(self, run_settings):
        if self.input_exists(run_settings):
            if self.input_platform_name:
                run_settings.setdefault(
                    django_settings.SCHEMA_PREFIX + '/platform/storage/input',
                    {})[u'platform_url'] = self.input_platform_name
            if self.input_platform_offset:
                run_settings[django_settings.SCHEMA_PREFIX + '/platform/storage/input']['offset'] = self.input_platform_offset


    def writeout_computation(self, run_settings):
        if self.compute_platform_name:
            run_settings.setdefault('%s/platform/computation' % django_settings.SCHEMA_PREFIX,
                {})[u'platform_url'] = self.compute_platform_name

        if self.compute_platform_offset:
            run_settings.setdefault('%s/platform/computation' % django_settings.SCHEMA_PREFIX,
                {})[u'offset'] = self.compute_platform_offset

        logger.debug('self.compute_platform_name=%s' % self.compute_platform_name)


    def output(self, run_settings):
        self.writeout_output(run_settings)
        self.writeout_input(run_settings)
        self.writeout_computation(run_settings)
        setval(run_settings,
               '%s/stages/configure/configure_done' % django_settings.SCHEMA_PREFIX,
               1)
        setval(run_settings,
               '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX,
               str(self.experiment_id))
        setval(run_settings,
               '%s/system/usage_logs' % django_settings.SCHEMA_PREFIX,
               self.NETWORK_IO_USAGE_LOG)


        return run_settings

    def copy_to_scratch_space(self, run_settings, local_settings, result_offset):
        bdp_username = run_settings['%s/bdp_userprofile' % django_settings.SCHEMA_PREFIX]['username']
        output_storage_url = run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)

        run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset'] = self.output_loc_offset
        offset = run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        iter_inputdir = os.path.join(self.job_dir, result_offset)
        logger.debug("iter_inputdir=%s" % iter_inputdir)

        input_storage_settings = self.get_platform_settings(run_settings, '%s/platform/storage/input' % django_settings.SCHEMA_PREFIX)
        #input_location = run_settings[django_settings.SCHEMA_PREFIX + '/input/system']['input_location']

        try:
            input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/system/input_location')
        except SettingNotFoundException:
            try:
		input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input_location')
	    except:
		input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input/input_location')
        logger.debug("input_location=%s" % input_location)
        #todo: input location will evenatually be replaced by the scratch space that was used by the sweep
        #todo: the sweep will indicate the location of the scratch space in the run_settings
        #todo: add scheme (ssh) to inputlocation

        #source_url = get_url_with_credentials(local_settings, input_location)

        input_offset = run_settings['%s/platform/storage/input' % django_settings.SCHEMA_PREFIX]['offset']
        input_url = "%s://%s@%s/%s" % (input_storage_settings['scheme'],
                                       input_storage_settings['type'],
                                       input_storage_settings['host'], input_offset)
        source_url = get_url_with_credentials(
            input_storage_settings, input_url, is_relative_path=False)

        logger.debug("source_url=%s" % source_url)

        destination_url = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                             output_storage_settings['type'],
                             iter_inputdir),
            is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        #storage.copy_directories(source_url, destination_url)
        storage.copy_directories(source_url, destination_url,job_id=str(self.contextid), message='ConfigureStage')


    def get_results_dirname(self, run_settings):
        try:
            name = getval(run_settings, '%s/directive_profile/directive_name' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            name = 'unknown_connector'
        output_loc_offset = str(self.contextid)
        logger.debug("suffix=%s" % output_loc_offset)
        try:
            #fixme, hrmc should be variable..so configure can be used in any connector
            output_loc_offset = os.path.join(
                run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset'],
                name + self.output_loc_offset)
        except KeyError:
            pass
        return output_loc_offset

    #def curate_data(self, run_settings, location, experiment_id):
    #    return experiment_id
