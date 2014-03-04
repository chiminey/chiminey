import logging
import os

from chiminey.corestages import Sweep
from chiminey import mytardis
from chiminey.platform import manage
from chiminey.runsettings import getval, getvals, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs, list_all_files, get_basename

logger = logging.getLogger(__name__)




class VASPSweep(Sweep):

    SCHEMA_PREFIX = "http://rmit.edu.au/schemas"

    def input_valid(self, settings_to_test):
        logger.debug('settings_to_test=%s' % settings_to_test)
        try:
                input_location = getval(settings_to_test, '%s/input/system/input_location' % self.SCHEMA_PREFIX)
        except SettingNotFoundException:
            input_location = getval(settings_to_test, '%s/input/location/input/input_location' % self.SCHEMA_PREFIX)
        input_platform_name, input_platform_offset = self.break_bdp_url(input_location)
        settings_to_test[self.SCHEMA_PREFIX + '/platform/storage/input'] = {}
        settings_to_test[self.SCHEMA_PREFIX + '/platform/storage/input'][
        'platform_url'] = input_platform_name
        settings_to_test[self.SCHEMA_PREFIX + '/platform/storage/input']['offset'] = input_platform_offset

        input_settings = self.get_platform_settings(
            settings_to_test, '%s/platform/storage/input' % self.SCHEMA_PREFIX)
        logger.debug('input-settings=%s' % input_settings)
        input_url = "%s://%s@%s/%s/initial" % (
            input_settings['scheme'], input_settings['type'],
            input_settings['host'], input_platform_offset)
        logger.debug('input_url=%s' % input_url)
        input_url_cred = get_url_with_credentials(input_settings, input_url, is_relative_path=False)
        expected_input_files = ['INCAR_template', 'KPOINTS_template', 'POSCAR', 'POTCAR', 'vasp_sub_template']
        provided_input_files = get_basename(list_all_files(input_url_cred))
        for file in expected_input_files:
            logger.debug('expected file %s' % file)
            if file not in provided_input_files:
                return (False, 'Expected VASP input files under initial/ not found. Expected %s; Provided %s'
                               % (expected_input_files, provided_input_files))
        return (True, 'valid_input')


    def curate_data(self, run_settings, location, experiment_id):

        logger.debug("vasp curate_data")
        try:
            subdirective = getval(run_settings, '%s/stages/sweep/directive' % self.SCHEMA_PREFIX)
        except SettingNotFoundException:
            logger.warn("cannot find subdirective name")
            subdirective = ''

        if subdirective == "vasp":

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
                    expname=ename,
                    experiment_paramset=[
                    mytardis.create_paramset("remotemake", []),
                    mytardis.create_graph_paramset("expgraph",
                        name="makeexp1",
                        graph_info={"axes":["num_kp", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp", "makedset/toten"]]),
                    mytardis.create_graph_paramset("expgraph",
                        name="makeexp2",
                        graph_info={"axes":["encut", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/encut", "makedset/toten"]]),
                    mytardis.create_graph_paramset("expgraph",
                        name="makeexp3",
                        graph_info={"axes":["num_kp", "encut", "TOTEN"], "legends":["TOTEN"]},
                        value_dict={},
                    value_keys=[["makedset/num_kp", "makedset/encut", "makedset/toten"]]),
                ])

        else:
            logger.warn("cannot find subdirective name")

        return experiment_id
