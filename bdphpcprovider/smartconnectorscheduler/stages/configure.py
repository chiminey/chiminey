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


from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import smartconnector, platform


from bdphpcprovider import mytardis
from bdphpcprovider import messages
from bdphpcprovider import storage


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Configure(Stage, UI):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number

    def triggered(self, run_settings):
        if self._exists(run_settings,
            RMIT_SCHEMA + '/stages/configure',
            'configure_done'):
            configure_done = int(run_settings[
                RMIT_SCHEMA + '/stages/configure'][u'configure_done'])
            return not configure_done
        return True

    def process(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)

        messages.info(run_settings, "1: configure")
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        logger.debug("settings=%s" % pformat(run_settings))
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/input/hrmc/optimisation_scheme')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/input/hrmc/threshold')
        local_settings['bdp_username'] = run_settings[
            RMIT_SCHEMA + '/bdp_userprofile']['username']
        logger.debug('local_settings=%s' % local_settings)

        input_location = run_settings[
            RMIT_SCHEMA + '/input/system']['input_location']
        logger.debug("input_location=%s" % input_location)

        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = platform.get_platform_settings(output_storage_url, bdp_username)

        input_storage_url = run_settings[
            RMIT_SCHEMA + '/platform/storage/input']['platform_url']
        input_storage_settings = platform.get_platform_settings(
            input_storage_url,
            bdp_username)
        input_offset = run_settings[RMIT_SCHEMA + "/platform/storage/input"]['offset']
        input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                    input_storage_settings['type'])
        map_initial_location = "%s/%s/initial" % (input_prefix, input_offset)
        logger.debug("map_initial_location=%s" % map_initial_location)

        self.contextid = int(run_settings[
            RMIT_SCHEMA + '/system'][u'contextid'])
        logger.debug("self.contextid=%s" % self.contextid)

        self.output_loc_offset = str(self.contextid)
        logger.debug("suffix=%s" % self.output_loc_offset)
        try:
            #fixme, hrmc should be variable..so configure can be used in any connector
            self.output_loc_offset = os.path.join(
                run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'],
                'hrmc' + self.output_loc_offset)
        except KeyError:
            pass
        run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = self.output_loc_offset

        self.job_dir = platform.get_job_dir(output_storage_settings, run_settings)
        iter_inputdir = os.path.join(self.job_dir, "input_0")
        logger.debug("iter_inputdir=%s" % iter_inputdir)
        #todo: input location will evenatually be replaced by the scratch space that was used by the sweep
        #todo: the sweep will indicate the location of the scratch space in the run_settings
        #todo: add scheme (ssh) to inputlocation
        source_url = smartconnector.get_url_with_pkey(local_settings,
            input_location)
        logger.debug("source_url=%s" % source_url)

        destination_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                             output_storage_settings['type'],
                             iter_inputdir),
            is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        storage.copy_directories(source_url, destination_url)

        output_location = self.output_loc_offset  # run_settings[RMIT_SCHEMA + '/input/system'][u'output_location']
        try:
            self.experiment_id = int(smartconnector.get_existing_key(run_settings,
                RMIT_SCHEMA + '/input/mytardis/experiment_id'))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
        mytardis_settings = platform.get_platform_settings(mytardis_url, bdp_username)
        logger.debug(mytardis_settings)
        #local_settings.update(mytardis_settings)

        if mytardis_settings['mytardis_host']:
            EXP_DATASET_NAME_SPLIT = 2

            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            ename = _get_exp_name_for_input(output_location)
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

    def output(self, run_settings):

        run_settings.setdefault(
            RMIT_SCHEMA + '/stages/configure',
            {})[u'configure_done'] = 1
        run_settings[RMIT_SCHEMA + '/input/mytardis']['experiment_id'] = str(self.experiment_id)
        run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = self.output_loc_offset
        return run_settings
