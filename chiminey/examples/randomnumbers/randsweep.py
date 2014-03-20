

import logging
import os

from chiminey.corestages import Sweep
from chiminey import mytardis
from chiminey.platform import manage
from chiminey.runsettings import getval, getvals, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs, list_all_files, get_basename
import json
import ast
logger = logging.getLogger(__name__)




class RandomNumbersSweep(Sweep):

    SCHEMA_PREFIX = "http://rmit.edu.au/schemas"

    def curate_data(self, run_settings, location, experiment_id):

        logger.debug("vasp curate_data")
        try:
            subdirective = getval(run_settings, '%s/stages/sweep/directive' % self.SCHEMA_PREFIX)
        except SettingNotFoundException:
            logger.warn("cannot find subdirective name")
            subdirective = ''

        if subdirective == "randomnumbers":

            bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % self.SCHEMA_PREFIX)
            mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
            logger.debug(mytardis_settings)

            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-2:]))

            ename = _get_exp_name_for_input(location)

            experiment_id = mytardis.create_experiment(
                    settings=mytardis_settings,
                    exp_id=experiment_id,
                    expname=ename)

        else:
            logger.warn("cannot find subdirective name")

        return experiment_id

