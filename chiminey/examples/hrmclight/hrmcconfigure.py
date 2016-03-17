import os
import logging

from chiminey.corestages import Configure

from chiminey.platform import manage
from chiminey import mytardis
from chiminey.runsettings import getval, SettingNotFoundException


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class HRMCConfigure(Configure):

    def curate_data(self, run_settings, location, experiment_id):
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']

        curate_data = run_settings['http://rmit.edu.au/schemas/input/mytardis']['curate_data']
        if curate_data:
            mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
            logger.debug(mytardis_settings)

            EXP_DATASET_NAME_SPLIT = 2

            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            hrmcexp = []
            for (sch, n) in (('hrmc', 'iseed'),
                      ('hrmc', 'pottype'),
                      ('hrmc', 'error_threshold'),
                      ('hrmc', 'optimisation_scheme'),
                      ('hrmc', 'fanout_per_kept_result'),
                      ('hrmc', 'threshold'),
                      ('hrmc', 'max_iteration'),
                      ('sweep', 'sweep_map'),
                      ('system', 'input_location'),
                      ('system', 'output_location'),
                      ('system/compplatform/cloud', 'computation_platform')
                       ):
                try:
                    hrmcexp.append({'name': n, 'value': getval(run_settings,
                                '%s/input/%s/%s' % (RMIT_SCHEMA, sch, n))})
                except SettingNotFoundException:
                    logger.warn('%s/input/%s/%s value not found' % (RMIT_SCHEMA, sch, n))

            logger.debug("location=%s" % location)
            ename = _get_exp_name_for_input(location)
            logger.debug("ename=%s" % ename)
            experiment_id = mytardis.create_experiment(
                settings=mytardis_settings,
                exp_id=experiment_id,
                expname=ename,
                experiment_paramset=[
                    mytardis.create_paramset("hrmcexp", hrmcexp),
                    mytardis.create_graph_paramset("expgraph",
                        name="hrmcexp",
                        graph_info={"axes":["iteration", "criterion"], "legends":["criterion"], "precision":[0, 2]},
                        value_dict={},
                        value_keys=[["hrmcdset/it", "hrmcdset/crit"]])
            ])

        else:
            logger.warn('Data curation is off')
        return experiment_id
