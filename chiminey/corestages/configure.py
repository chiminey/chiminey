# Copyright (C) 2013, RMIT University

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

from chiminey.corestages.stage import Stage, UI
from chiminey.smartconnectorscheduler import models

from chiminey import mytardis
from chiminey import messages
from chiminey import storage

from chiminey.runsettings import getval, getvals, setval, update, SettingNotFoundException
from chiminey.storage import get_url_with_credentials


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Configure(Stage):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number

    def is_triggered(self, run_settings):
        try:
            configure_done = int(getval(run_settings,
                '%s/stages/configure/configure_done' % RMIT_SCHEMA))
        except SettingNotFoundException:
            return True
        except ValueError:
            return True
        else:
            return not configure_done


    def process(self, run_settings):

        logger.debug('run_settings=%s' % run_settings)
        self.output_platform_name = ''
        self.output_platform_offset = ''
        self.input_platform_name = ''
        self.input_platform_offset = ''
        self.compute_platform_name = ''
        self.compute_platform_offset = ''
        if self.output_exists(run_settings):
            try:
                 run_settings['http://rmit.edu.au/schemas/platform/storage/output']
            except KeyError:
                logger.debug('bdp_url settings ...')
                try:
                    bdp_url = getval(run_settings, RMIT_SCHEMA + '/input/system/output_location')
                    logger.debug('bdp_url=%s' % bdp_url)
                except SettingNotFoundException:
                    bdp_url = getval(run_settings, RMIT_SCHEMA + '/input/location/output/output_location')
                    logger.debug('bdp_url=%s' % bdp_url)
                self.output_platform_name, self.output_platform_offset = self.break_bdp_url(bdp_url)
                run_settings[RMIT_SCHEMA + '/platform/storage/output'] = {}
                run_settings[RMIT_SCHEMA + '/platform/storage/output'][
                'platform_url'] = self.output_platform_name
                run_settings[RMIT_SCHEMA + '/platform/storage/output']['offset'] = self.output_platform_offset

        if self.input_exists(run_settings):
            try:
                 run_settings['http://rmit.edu.au/schemas/platform/storage/input']
            except KeyError:
                try:
                    bdp_url = getval(run_settings, RMIT_SCHEMA + '/input/system/input_location')
                except SettingNotFoundException:
                    bdp_url = getval(run_settings, RMIT_SCHEMA + '/input/location/input/input_location')
                self.input_platform_name, self.input_platform_offset = self.break_bdp_url(bdp_url)
                run_settings[RMIT_SCHEMA + '/platform/storage/input'] = {}
                run_settings[RMIT_SCHEMA + '/platform/storage/input'][
                'platform_url'] = self.input_platform_name
                run_settings[RMIT_SCHEMA + '/platform/storage/input']['offset'] = self.input_platform_offset

        try:
             run_settings['http://rmit.edu.au/schemas/platform/computation']
        except KeyError:
            bdp_url =  run_settings[RMIT_SCHEMA + '/input/system/compplatform']['computation_platform']
            logger.debug('tbdp_url=%s' % bdp_url)
            self.compute_platform_name, self.compute_platform_offset = self.break_bdp_url(bdp_url)
            run_settings[RMIT_SCHEMA + '/platform/computation'] = {}
            run_settings[RMIT_SCHEMA + '/platform/computation']['platform_url'] = self.compute_platform_name
            run_settings[RMIT_SCHEMA + '/platform/computation']['offset'] = self.compute_platform_offset

        messages.info(run_settings, "1: configure")

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)

        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        logger.debug("settings=%s" % pformat(run_settings))

        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

        # local_settings['bdp_username'] = run_settings[
        #     RMIT_SCHEMA + '/bdp_userprofile']['username']


        logger.debug('local_settings=%s' % local_settings)

        #input_location = getval(run_settings, "%s/input/system/input_location" % RMIT_SCHEMA)
        # input_location = run_settings[
        #     RMIT_SCHEMA + '/input/system']['input_location']
        #logger.debug("input_location=%s" % input_location)

        bdp_username = local_settings['bdp_username']

        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
        # output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        #output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)


        #input_storage_url = getval(run_settings, '%s/platform/storage/input/platform_url' % RMIT_SCHEMA)
        #input_storage_settings = manage.get_platform_settings(
        #    input_storage_url,
        #    bdp_username)

        #input_offset = getval(run_settings, '%s/platform/storage/input/offset' % RMIT_SCHEMA)
        #input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
        #                            input_storage_settings['type'])
        #map_initial_location = "%s/%s/initial" % (input_prefix, input_offset)
        #logger.debug("map_initial_location=%s" % map_initial_location)

        self.contextid = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)
        logger.debug("self.contextid=%s" % self.contextid)
        self.output_loc_offset = str(self.contextid)

        '''
        self.output_loc_offset = str(self.contextid)
        logger.debug("suffix=%s" % self.output_loc_offset)
        try:
            #fixme, hrmc should be variable..so configure can be used in any connector
            off = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
            self.output_loc_offset = os.path.join(off,
               'hrmc' + self.output_loc_offset)
        except SettingNotFoundException:
            pass
        '''
        self.output_loc_offset = self.get_results_dirname(run_settings)
        logger.debug('self.output_loc_offset=%s' % self.output_loc_offset)
        if self.input_exists(run_settings):
            self.copy_to_scratch_space(run_settings, local_settings)
        '''
        run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = self.output_loc_offset
        offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        iter_inputdir = os.path.join(self.job_dir, "input_0")
        logger.debug("iter_inputdir=%s" % iter_inputdir)
        #todo: input location will evenatually be replaced by the scratch space that was used by the sweep
        #todo: the sweep will indicate the location of the scratch space in the run_settings
        #todo: add scheme (ssh) to inputlocation
        source_url = get_url_with_credentials(local_settings,
            input_location)
        logger.debug("source_url=%s" % source_url)

        destination_url = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                             output_storage_settings['type'],
                             iter_inputdir),
            is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        storage.copy_directories(source_url, destination_url)
        '''

        output_location = self.output_loc_offset  # run_settings[RMIT_SCHEMA + '/input/system'][u'output_location']

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0
        try:
            curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
        except SettingNotFoundException:
            curate_data = False
        if curate_data:
            self.experiment_id = self.curate_data(run_settings,
                output_location, self.experiment_id)

        '''

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        #     self.experiment_id = int(stage.get_existing_key(run_settings,
        #         RMIT_SCHEMA + '/input/mytardis/experiment_id'))
        # except KeyError:
        #     self.experiment_id = 0
        # except ValueError:
        #     self.experiment_id = 0

        curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)

        if curate_data:

            mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
            logger.debug(mytardis_settings)
            #local_settings.update(mytardis_settings)

            if mytardis_settings['mytardis_host']:
                EXP_DATASET_NAME_SPLIT = 2

                def _get_exp_name_for_input(path):
                    return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                #ename = _get_exp_name_for_input(output_location)
                ename = _get_exp_name_for_input(self.output_loc_offset)
                logger.debug("ename=%s" % ename)
                self.experiment_id = mytardis.create_experiment(
                    settings=mytardis_settings,
                    exp_id=self.experiment_id,
                    expname=ename,
                    experiment_paramset=[
                        mytardis.create_paramset("hrmcexp", []),
                        mytardis.create_graph_paramset("expgraph",
                            name="hrmcexp",
                            graph_info={"axes":["iteration", "criterion"], "legends":["criterion"], "precision":[0, 2]},
                            value_dict={},
                            value_keys=[["hrmcdset/it", "hrmcdset/crit"]])
                ])
            else:
                logger.warn("no mytardis host specified")
        else:
            logger.warn('Data curation is off')
        '''

    def output(self, run_settings):
        setval(run_settings,
               '%s/stages/configure/configure_done' % RMIT_SCHEMA,
               1)
        setval(run_settings,
               '%s/input/mytardis/experiment_id' % RMIT_SCHEMA,
               str(self.experiment_id))
        if self.output_exists(run_settings):
            if self.output_platform_name:
                run_settings.setdefault(
                    RMIT_SCHEMA + '/platform/storage/output',
                    {})[u'platform_url'] = self.output_platform_name
            #if self.output_platform_offset:
            #    run_settings[RMIT_SCHEMA + '/platform/storage/output']['offset'] = self.output_platform_offset
            #else:
            run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = self.output_loc_offset

        if self.input_exists(run_settings):
            if self.input_platform_name:
                run_settings.setdefault(
                    RMIT_SCHEMA + '/platform/storage/input',
                    {})[u'platform_url'] = self.input_platform_name
            if self.input_platform_offset:
                run_settings[RMIT_SCHEMA + '/platform/storage/input']['offset'] = self.input_platform_offset

        logger.debug('self.compute_platform_name=%s' % self.compute_platform_name)
        if self.compute_platform_name:
            run_settings.setdefault('http://rmit.edu.au/schemas/platform/computation',
                {})[u'platform_url'] = self.compute_platform_name

        if self.compute_platform_offset:
            run_settings.setdefault('http://rmit.edu.au/schemas/platform/computation',
                {})[u'offset'] = self.compute_platform_offset

        return run_settings

    def copy_to_scratch_space(self, run_settings, local_settings):
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)

        run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = self.output_loc_offset
        offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        iter_inputdir = os.path.join(self.job_dir, "input_0")
        logger.debug("iter_inputdir=%s" % iter_inputdir)

        input_location = run_settings[
            RMIT_SCHEMA + '/input/system']['input_location']
        logger.debug("input_location=%s" % input_location)
        #todo: input location will evenatually be replaced by the scratch space that was used by the sweep
        #todo: the sweep will indicate the location of the scratch space in the run_settings
        #todo: add scheme (ssh) to inputlocation
        source_url = get_url_with_credentials(local_settings, input_location)
        logger.debug("source_url=%s" % source_url)

        destination_url = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                             output_storage_settings['type'],
                             iter_inputdir),
            is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        storage.copy_directories(source_url, destination_url)


    def get_results_dirname(self, run_settings):
        try:
            name = getval(run_settings, '%s/directive_profile/directive_name' % RMIT_SCHEMA)
        except SettingNotFoundException:
            name = 'unknown_connector'
        output_loc_offset = str(self.contextid)
        logger.debug("suffix=%s" % output_loc_offset)
        try:
            #fixme, hrmc should be variable..so configure can be used in any connector
            output_loc_offset = os.path.join(
                run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'],
                name + self.output_loc_offset)
        except KeyError:
            pass
        return output_loc_offset

    def curate_data(self, run_settings, location, experiment_id):
        return experiment_id

