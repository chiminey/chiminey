
import logging

from chiminey.corestages import Sweep


from chiminey import mytardis

from chiminey.runsettings import getval, SettingNotFoundException


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"
FIRST_ITERATION_DIR = "input_0"
SUBDIRECTIVE_DIR = "run%(run_counter)s"

VALUES_MAP_TEMPLATE_FILE = '%(template_name)s_values'
VALUES_MAP_FILE = "values"


class VASPSweep(Sweep):

    def curate_data(self, run_settings, experiment_id):

        try:
            subdirective = getval(run_settings, '%s/stages/sweep/directive' % RMIT_SCHEMA)
        except SettingNotFoundException:
            logger.warn("cannot find subdirective name")
            subdirective = ''

        if subdirective == "vasp":
            experiment_id = self.post_mytardis_exp(
                run_settings=run_settings,
                experiment_id=experiment_id,
                output_location=self.scratch_platform,
                experiment_paramset=[
                    mytardis.make_paramset("remotemake", []),
                    mytardis.make_graph_paramset("expgraph",
                        name="makeexp1",
                        graph_info={"axes":["num_kp", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp", "makedset/toten"]]),
                    mytardis.make_graph_paramset("expgraph",
                        name="makeexp2",
                        graph_info={"axes":["encut", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/encut", "makedset/toten"]]),
                    mytardis.make_graph_paramset("expgraph",
                        name="makeexp3",
                        graph_info={"axes":["num_kp", "encut", "TOTEN"], "legends":["TOTEN"]},
                        value_dict={},
                    value_keys=[["makedset/num_kp", "makedset/encut", "makedset/toten"]]),
                                ])
        else:
            logger.warn("cannot find subdirective name")

        return experiment_id
