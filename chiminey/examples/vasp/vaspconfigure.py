import logging
import os

from chiminey.corestages.configure import Configure
from chiminey import mytardis
from chiminey.platform import manage
from chiminey.runsettings import getval, SettingNotFoundException

logger = logging.getLogger(__name__)

class VASPConfigure(Configure):

    SCHEMA_PREFIX = "http://rmit.edu.au/schemas"

    def curate_data(self, run_settings, location, experiment_id):
        logger.debug("vasp curate_data")
        logger.debug('location=%s' % location)
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
        return experiment_id




        #else:
        #    logger.warn("cannot find subdirective name")

