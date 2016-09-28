import os, logging, re

from django.conf import settings as django_settings
from chiminey.mytardis.metadata import MetadataBuilder
from chiminey.mytardis import mytardis
from chiminey import storage
from chiminey.runsettings import getval


logger = logging.getLogger(__name__)

class HRMCMetadataBuilder(MetadataBuilder):
    DATA_ERRORS_FILE = "data_errors.dat"
    STEP_COLUMN_NUM = 0
    ERRGR_COLUMN_NUM = 28
    final_graph_paramset = []

    def build_experiment_metadata(self, **kwargs):
        experiment_paramset = [mytardis.create_paramset("hrmcexp", []),
            mytardis.create_graph_paramset("expgraph",
            name="hrmcexp",
            graph_info={"axes":["iteration", "criterion"], "legends":["criterion"], "precision":[0, 2]},
            value_dict={},
            value_keys=[["hrmcdset/it", "hrmcdset/crit"]])]
        logger.debug('experiment_paramset=%s' % experiment_paramset)
        return experiment_paramset

    def build_metadata_for_inputs(self, **kwargs):
        experiment_paramset = []
        dataset_paramset=[mytardis.create_paramset('hrmcdataset/input', [])]
        logger.debug('experiment_paramset=%s, dataset_paramset=%s' % \
        (experiment_paramset, dataset_paramset))
        return experiment_paramset, dataset_paramset


    def build_metadata_for_intermediate_output(self, output_dir,
     outputs, **kwargs):
        continue_loop = True
        node_output_dirname = os.path.basename(output_dir)
        # find criterion
        crit = None  # is there an infinity criterion
        for ni in outputs:
            if ni.dirname == node_output_dirname:
                crit = ni.criterion
                continue_loop = False
                break
        if continue_loop:
            logger.debug("criterion not found")
            return (continue_loop, [], [], {})
        logger.debug("crit=%s" % crit)

        def extract_psd_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
            return res

        def extract_psdexp_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            res = {"hrmcdfile/r2": xs, "hrmcdfile/g2": ys}
            return res

        def extract_grfinal_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            #FIXME: len(xs) == len(ys) for this to work.
            #TODO: hack to handle when xs and ys are too
            # large to fit in Parameter with db_index.
            # solved by function call at destination
            cut_xs = [xs[i] for i, x in enumerate(xs)
                if (i % (len(xs) / 20) == 0)]
            cut_ys = [ys[i] for i, x in enumerate(ys)
                if (i % (len(ys) / 20) == 0)]

            res = {"hrmcdfile/r3": cut_xs, "hrmcdfile/g3": cut_ys}
            return res

        def extract_inputgr_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            #FIXME: len(xs) == len(ys) for this to work.
            #TODO: hack to handle when xs and ys are too
            # large to fit in Parameter with db_index.
            # solved by function call at destination
            cut_xs = [xs[i] for i, x in enumerate(xs)
                if (i % (len(xs) / 20) == 0)]
            cut_ys = [ys[i] for i, x in enumerate(ys)
                if (i % (len(ys) / 20) == 0)]

            res = {"hrmcdfile/r4": cut_xs, "hrmcdfile/g4": cut_ys}
            return res

        system_id = int(getval(kwargs['run_settings'], '%s/system/id' % django_settings.SCHEMA_PREFIX))
        dataset_paramset=[
            mytardis.create_paramset("hrmcdataset/output", []),
            mytardis.create_graph_paramset("dsetgraph",
                name="hrmcdset",
                graph_info={"axes":["r (Angstroms)", "PSD"],
                    "legends":["psd", "PSD_exp"], "type":"line"},
                value_dict={"hrmcdset/it": system_id,
                     "hrmcdset/crit": crit},
                value_keys=[["hrmcdfile/r1", "hrmcdfile/g1"],
                    ["hrmcdfile/r2", "hrmcdfile/g2"]]
                ),
            mytardis.create_graph_paramset("dsetgraph",
                name="hrmcdset2",
                graph_info={"axes":["r (Angstroms)", "g(r)"],
                    "legends":["data_grfinal", "input_gr"],
                    "type":"line"},
                value_dict={},
                value_keys=[["hrmcdfile/r3", "hrmcdfile/g3"],
                    ["hrmcdfile/r4", "hrmcdfile/g4"]]
                ),
            ]
        datafile_paramset=[
            mytardis.create_graph_paramset("dfilegraph",
                name="hrmcdfile",
                graph_info={},
                value_dict={},
                value_keys=[])
            ]
        dfile_extract_func={
            'psd.dat': extract_psd_func,
            'PSD_exp.dat': extract_psdexp_func,
            'data_grfinal.dat': extract_grfinal_func,
            'input_gr.dat': extract_inputgr_func
            }
        logger.debug('dataset_paramset=%s, datafile_paramset=%s, dfile_extract_func=%s ' % \
        (dataset_paramset, datafile_paramset, dfile_extract_func))

        return (continue_loop, dataset_paramset, datafile_paramset, dfile_extract_func)

    def build_metadata_for_final_output(self, m, output_dir, **kwargs):
        #FIXME: this calculation should be done as in extract_psd_func
        # pulling directly from data_errors rather than passing in
        # through nested function.
        experiment_paramset = []
        dataset_paramset = []
        datafile_paramset = []
        dfile_extract_func = {}

        exp_value_keys = []
        legends = []
        for m, current_dir in enumerate(kwargs['output_dirs']):
            #node_path = os.path.join(iter_output_dir, node_dir)

            exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

            source_url = storage.get_url_with_credentials(\
            kwargs['storage_settings'], current_dir, is_relative_path=False)

            (source_scheme, source_location, source_path, source_location,
                query_settings) = storage.parse_bdpurl(source_url)
            logger.debug("source_url=%s" % source_url)
            legends.append(
                mytardis.get_dataset_name_for_output(
                    kwargs['storage_settings'], "", source_path))

        logger.debug("exp_value_keys=%s" % exp_value_keys)
        logger.debug("legends=%s" % legends)




        # for m, output_dir in enumerate(kwargs['output_dirs']):
        #node_path = os.path.join(iter_output_dir, output_dir)
        node_path = output_dir
        logger.debug("node_path=%s" % node_path)

        dataerrors_url = storage.get_url_with_credentials(kwargs['storage_settings'],
            os.path.join(node_path, self.DATA_ERRORS_FILE),
            is_relative_path=False)
        logger.debug("dataerrors_url=%s" % dataerrors_url)
        dataerrors_content = storage.get_file(dataerrors_url)
        xs = []
        ys = []
        re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')
        for i, line in enumerate(dataerrors_content.splitlines()):
            if i == 0:
                continue
            columns = line.split()
            try:
                hrmc_step = int(columns[self.STEP_COLUMN_NUM])
            except ValueError:
                logger.warn("could not parse hrmc_step value on line %s" % i)
                continue
            # handle  format double precision float format
            val = columns[self.ERRGR_COLUMN_NUM]
            val = re_dbl_fort.sub(r'\1E\2', val)
            logger.debug("val=%s" % val)
            try:
                hrmc_errgr = float(val)
            except ValueError:
                logger.warn("could not parse hrmc_errgr value on line %s" % i)
                continue
            xs.append(hrmc_step)
            ys.append(hrmc_errgr)

        logger.debug("xs=%s" % xs)
        logger.debug("ys=%s" % ys)

        crit_url = storage.get_url_with_credentials(kwargs['storage_settings'],
            os.path.join(node_path, "criterion.txt"), is_relative_path=False)
        try:
            crit = storage.get_file(crit_url)
        except ValueError:
            crit = None
        except IOError:
            crit = None
        # FIXME: can crit be zero?
        logger.debug("crit=%s" % crit)
        if crit:
            system_id = int(getval(kwargs['run_settings'], '%s/system/id' % \
            django_settings.SCHEMA_PREFIX))
            hrmcdset_val = {"hrmcdset/it": system_id, "hrmcdset/crit": crit}
        else:
            hrmcdset_val = {}

        # TODO: move into utiltiy function for reuse
        def extract_psd_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(dataerrors_content.splitlines()):
                if i == 0:
                    continue
                columns = line.split()

                val = columns[self.STEP_COLUMN_NUM]
                val = re_dbl_fort.sub(r'\1E\2', val)
                logger.debug("val=%s" % val)
                try:
                    x = float(val)
                except ValueError:
                    logger.warn("could not parse value on line %s" % i)
                    continue

                val = columns[self.ERRGR_COLUMN_NUM]
                val = re_dbl_fort.sub(r'\1E\2', val)
                logger.debug("val=%s" % val)
                try:
                    y = float(val)
                except ValueError:
                    logger.warn("could not parse value on line %s" % i)
                    continue

                xs.append(x)
                ys.append(y)
            res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
            return res

        def extract_psdexp_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            res = {"hrmcdfile/r2": xs, "hrmcdfile/g2": ys}
            return res

        def extract_grfinal_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            #FIXME: len(xs) == len(ys) for this to work.
            #TODO: hack to handle when xs and ys are too
            # large to fit in Parameter with db_index.
            # solved by function call at destination
            cut_xs = [xs[i] for i, x in enumerate(xs)
                if (i % (len(xs) / 50) == 0)]
            cut_ys = [ys[i] for i, x in enumerate(ys)
                if (i % (len(ys) / 50) == 0)]

            res = {"hrmcdfile/r3": cut_xs, "hrmcdfile/g3": cut_ys}
            return res

        def extract_inputgr_func(fp):
            res = []
            xs = []
            ys = []
            for i, line in enumerate(fp):
                columns = line.split()
                xs.append(float(columns[0]))
                ys.append(float(columns[1]))
            #FIXME: len(xs) == len(ys) for this to work.
            #TODO: hack to handle when xs and ys are too
            # large to fit in Parameter with db_index.
            # solved by function call at destination
            cut_xs = [xs[i] for i, x in enumerate(xs)
                if (i % (len(xs) / 50) == 0)]
            cut_ys = [ys[i] for i, x in enumerate(ys)
                if (i % (len(ys) / 50) == 0)]

            res = {"hrmcdfile/r4": cut_xs, "hrmcdfile/g4": cut_ys}
            return res
        #todo: replace self.boto_setttings with mytardis_settings


        # Only save graph paramset for experiment once per experiment.
        if not self.final_graph_paramset:
            self.final_graph_paramset = [mytardis.create_graph_paramset("expgraph",
                name="hrmcexp2",
                graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
                value_dict={},
                value_keys=exp_value_keys)]

            experiment_paramset = self.final_graph_paramset
        else:
            experiment_paramset = []

        dataset_paramset = [
            mytardis.create_paramset('hrmcdataset/output', []),
            mytardis.create_graph_paramset('dsetgraph',
                name="hrmcdset",
                graph_info={"axes":["r (Angstroms)", "PSD"],
                    "legends":["psd", "PSD_exp"],  "type":"line"},
                value_dict=hrmcdset_val,
                value_keys=[["hrmcdfile/r1", "hrmcdfile/g1"],
                    ["hrmcdfile/r2", "hrmcdfile/g2"]]),
            mytardis.create_graph_paramset('dsetgraph',
                name='hrmcdset2',
                graph_info={"axes":["r (Angstroms)", "g(r)"],
                    "legends":["data_grfinal", "input_gr"],
                    "type":"line"},
                value_dict={},
                value_keys=[["hrmcdfile/r3", "hrmcdfile/g3"],
                    ["hrmcdfile/r4", "hrmcdfile/g4"]]),
            mytardis.create_graph_paramset('dsetgraph',
                name='hrmcdset%s' % m,
                graph_info={},
                value_dict={"hrmcdset%s/step" % m: xs,
                    "hrmcdset%s/err" % m: ys},
                value_keys=[]),
            ]
        datafile_paramset = [
            mytardis.create_graph_paramset('dfilegraph',
                name="hrmcdfile",
                graph_info={},
                value_dict={},
                value_keys=[])
            ]
        dfile_extract_func = {
            'psd.dat': extract_psd_func,
            'PSD_exp.dat': extract_psdexp_func,
            'data_grfinal.dat': extract_grfinal_func,
            'input_gr.dat': extract_inputgr_func}
        logger.debug("experiment_paramset=%s" % experiment_paramset)
        logger.debug("dataset_paramset=%s" % dataset_paramset)
        logger.debug("datafile_paramset=%s" % datafile_paramset)
        logger.debug("dfile_extract_func=%s" % dfile_extract_func)

        return (experiment_paramset, dataset_paramset, datafile_paramset, dfile_extract_func)
