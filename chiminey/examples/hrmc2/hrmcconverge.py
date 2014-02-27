

# Copyright (C) 2012, RMIT University

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


import re
import os
import logging
import json
import sys
from chiminey.smartconnectorscheduler.errors import BadInputException
from chiminey.storage import get_url_with_credentials
from chiminey import storage
from chiminey import mytardis
from chiminey.runsettings import getval, SettingNotFoundException
from chiminey.corestages import Converge

logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"
DATA_ERRORS_FILE = "data_errors.dat"
STEP_COLUMN_NUM = 0
ERRGR_COLUMN_NUM = 28


class HRMCConverge(Converge):

    SCHEMA_PREFIX = "http://rmit.edu.au/schemas"
    VALUES_FNAME = "values"

    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem
        """
        error = []
        try:
            int(getval(settings_to_test, '%s/input/hrmc/max_iteration' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            error.append("Cannot load max_iteration")

        try:
            float(getval(settings_to_test, '%s/input/hrmc/error_threshold' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            error.append("Cannot load error threshold")

        if error:
            return (False, '. '.join(error))
        return (True, "ok")

    def curate_dataset(self, run_settings, experiment_id, base_dir, output_url, all_settings):
        logger.debug("curate_dataset")
        iter_output_dir = os.path.join(os.path.join(base_dir, "output"))
        logger.debug("iter_output_dir=%s" % iter_output_dir)

        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)
        logger.debug("iter_output_dir=%s" % iter_output_dir)
        logger.debug("output_url=%s" % output_url)
        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        fsys = storage.get_filesystem(output_url)

        node_output_dirnames, _ = fsys.listdir(mypath)
        logger.debug("node_output_dirnames=%s" % node_output_dirnames)

        curate_data = (getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA))
        if curate_data:
            if all_settings['mytardis_host']:

#         if mytardis_settings['mytardis_host']:

#             EXP_DATASET_NAME_SPLIT = 2

#             def get_exp_name_for_output(settings, url, path):
#                 return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

#             def get_dataset_name_for_output(settings, url, path):
#                 logger.debug("path=%s" % path)

#                 host = settings['host']
#                 prefix = 'ssh://%s@%s' % (settings['type'], host)

#                 source_url = smartconnectorscheduler.get_url_with_credentials(
#                     settings, os.path.join(prefix, path, "HRMC.inp_values"),
#                     is_relative_path=False)
#                 logger.debug("source_url=%s" % source_url)
#                 try:
#                     content = storage.get_file(source_url)
#                 except IOError, e:
#                     logger.warn("cannot read file %s" % e)
#                     return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

#                 logger.debug("content=%s" % content)
#                 try:
#                     values_map = dict(json.loads(str(content)))
#                 except Exception, e:
#                     logger.error("cannot load values_map %s: from %s.  Error=%s" % (content, source_url, e))
#                     return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

#                 try:
#                     iteration = str(path.split(os.sep)[-2:-1][0])
#                 except Exception, e:
#                     logger.error(e)
#                     iteration = ""

#                 if "_" in iteration:
#                     iteration = iteration.split("_")[1]
#                 else:
#                     iteration = "final"

#                 dataset_name = "%s_%s_%s" % (iteration,
#                     values_map['generator_counter'],
#                     values_map['run_counter'])
#                 logger.debug("dataset_name=%s" % dataset_name)
#                 return dataset_name

#             re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

#             logger.debug("new_output_dir=%s" % new_output_dir)
#             exp_value_keys = []
#             legends = []
#             for m, node_dir in enumerate(node_dirs):
#                 exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

#                 source_url = smartconnectorscheduler.get_url_with_credentials(output_storage_settings,
#                     output_prefix + os.path.join(new_output_dir, node_dir), is_relative_path=False)

#                 (source_scheme, source_location, source_path, source_location,
#                     query_settings) = storage.parse_bdpurl(source_url)
#                 logger.debug("source_url=%s" % source_url)
#                 legends.append(
#                     get_dataset_name_for_output(
#                         output_storage_settings, "", source_path))

#             logger.debug("exp_value_keys=%s" % exp_value_keys)
#             logger.debug("legends=%s" % legends)

#             graph_paramset = [mytardis.create_graph_paramset("expgraph",
#                 name="hrmcexp2",
#                 graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
#                 value_dict={},
#                 value_keys=exp_value_keys)]

#             for m, node_dir in enumerate(node_dirs):

#                 dataerrors_url = smartconnectorscheduler.get_url_with_credentials(output_storage_settings,
#                     output_prefix + os.path.join(new_output_dir, node_dir, DATA_ERRORS_FILE), is_relative_path=False)
#                 dataerrors_content = storage.get_file(dataerrors_url)
#                 xs = []
#                 ys = []
#                 for i, line in enumerate(dataerrors_content.splitlines()):
#                     if i == 0:
#                         continue
#                     columns = line.split()
#                     try:
#                         hrmc_step = int(columns[STEP_COLUMN_NUM])
#                     except ValueError:
#                         logger.warn("could not parse hrmc_step value on line %s" % i)
#                         continue
#                     # handle  format double precision float format
#                     val = columns[ERRGR_COLUMN_NUM]
#                     val = re_dbl_fort.sub(r'\1E\2', val)
#                     logger.debug("val=%s" % val)





                EXP_DATASET_NAME_SPLIT = 2

                def get_exp_name_for_output(settings, url, path):
                    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

                def get_dataset_name_for_output(settings, url, path):
                    logger.debug("path=%s" % path)

                    host = settings['host']
                    prefix = 'ssh://%s@%s' % (settings['type'], host)

                    source_url = get_url_with_credentials(
                        settings, os.path.join(prefix, path, self.VALUES_FNAME),
                        is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)
                    try:
                        content = storage.get_file(source_url)
                    except IOError, e:
                        logger.warn("cannot read file %s" % e)
                        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    logger.debug("content=%s" % content)
                    try:
                        values_map = dict(json.loads(str(content)))
                    except Exception, e:
                        logger.error("cannot load values_map %s: from %s.  Error=%s" % (content, source_url, e))
                        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    try:
                        iteration = str(path.split(os.sep)[-2:-1][0])
                    except Exception, e:
                        logger.error(e)
                        iteration = ""

                    if "_" in iteration:
                        iteration = iteration.split("_")[1]
                    else:
                        iteration = "final"

                    dataset_name = "%s_%s_%s" % (iteration,
                        values_map['generator_counter'],
                        values_map['run_counter'])
                    logger.debug("dataset_name=%s" % dataset_name)
                    return dataset_name

                re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

                exp_value_keys = []
                legends = []
                for m, node_dir in enumerate(node_output_dirnames):
                    node_path = os.path.join(iter_output_dir, node_dir)

                    exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

                    source_url = get_url_with_credentials(all_settings,
                                                   node_path, is_relative_path=False)

                    (source_scheme, source_location, source_path, source_location,
                        query_settings) = storage.parse_bdpurl(source_url)
                    logger.debug("source_url=%s" % source_url)
                    legends.append(
                        get_dataset_name_for_output(
                            all_settings, "", source_path))

                logger.debug("exp_value_keys=%s" % exp_value_keys)
                logger.debug("legends=%s" % legends)

                graph_paramset = [mytardis.create_graph_paramset("expgraph",
                    name="hrmcexp2",
                    graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
                    value_dict={},
                    value_keys=exp_value_keys)]

                for m, node_dir in enumerate(node_output_dirnames):
                    node_path = os.path.join(iter_output_dir, node_dir)
                    logger.debug("node_path=%s" % node_path)

                    #FIXME: this calculation should be done as in extract_psd_func
                    # pulling directly from data_errors rather than passing in
                    # through nested function.
                    dataerrors_url = get_url_with_credentials(all_settings,
                        os.path.join(node_path, DATA_ERRORS_FILE),
                        is_relative_path=False)
                    logger.debug("dataerrors_url=%s" % dataerrors_url)
                    dataerrors_content = storage.get_file(dataerrors_url)
                    xs = []
                    ys = []
                    for i, line in enumerate(dataerrors_content.splitlines()):
                        if i == 0:
                            continue
                        columns = line.split()
                        try:
                            hrmc_step = int(columns[STEP_COLUMN_NUM])
                        except ValueError:
                            logger.warn("could not parse hrmc_step value on line %s" % i)
                            continue
                        # handle  format double precision float format
                        val = columns[ERRGR_COLUMN_NUM]
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

                    crit_url = get_url_with_credentials(all_settings,
                        os.path.join(node_path, "criterion.txt"), is_relative_path=False)
                    try:
                        crit = storage.get_file(crit_url)
                    except ValueError:
                        crit = None
                    except IOError:
                        crit = None
                    # FIXME: can crit be zero?
                    if crit:
                        hrmcdset_val = {"hrmcdset/it": self.id, "hrmcdset/crit": crit}
                    else:
                        hrmcdset_val = {}

                    source_url = get_url_with_credentials(
                        all_settings, node_path, is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)

                    # TODO: move into utiltiy function for reuse
                    def extract_psd_func(fp):
                        res = []
                        xs = []
                        ys = []
                        for i, line in enumerate(dataerrors_content.splitlines()):
                            if i == 0:
                                continue
                            columns = line.split()

                            val = columns[STEP_COLUMN_NUM]
                            val = re_dbl_fort.sub(r'\1E\2', val)
                            logger.debug("val=%s" % val)
                            try:
                                x = float(val)
                            except ValueError:
                                logger.warn("could not parse value on line %s" % i)
                                continue

                            val = columns[ERRGR_COLUMN_NUM]
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
                    #todo: replace self.boto_setttings with mytardis_settings

                    experiment_id = mytardis.create_dataset(
                        settings=all_settings,
                        source_url=source_url,
                        exp_name=get_exp_name_for_output,
                        dataset_name=get_dataset_name_for_output,
                        exp_id=experiment_id,
                        experiment_paramset=graph_paramset,
                        dataset_paramset=[
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
                            ],
                        datafile_paramset=[
                            mytardis.create_graph_paramset('dfilegraph',
                                name="hrmcdfile",
                                graph_info={},
                                value_dict={},
                                value_keys=[])
                            ],
                        dfile_extract_func={
                            'psd.dat': extract_psd_func,
                             'PSD_exp.dat': extract_psdexp_func,
                             'data_grfinal.dat': extract_grfinal_func,
                             'input_gr.dat': extract_inputgr_func}

                        )
                    graph_paramset = []
            else:
                logger.warn("no mytardis host specified")
        else:
            logger.warn('Data curation is off')
        return experiment_id

    def process_outputs(self, run_settings, base_dir, input_url, all_settings):

        id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        iter_output_dir = os.path.join(os.path.join(base_dir, "input_%s" % (id + 1)))
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)

        (scheme, host, iter_output_path, location, query_settings) = storage.parse_bdpurl(input_url)
        iter_out_fsys = storage.get_filesystem(input_url)

        input_dirs, _ = iter_out_fsys.listdir(iter_output_path)

        # TODO: store all audit info in single file in input_X directory in transform,
        # so we do not have to load individual files within node directories here.
        min_crit = sys.float_info.max - 1.0
        min_crit_index = sys.maxint

        # # TODO: store all audit info in single file in input_X directory in transform,
        # # so we do not have to load individual files within node directories here.
        # min_crit = sys.float_info.max - 1.0
        # min_crit_index = sys.maxint
        logger.debug("input_dirs=%s" % input_dirs)
        for input_dir in input_dirs:
            node_path = os.path.join(iter_output_dir, input_dir)
            logger.debug('node_path= %s' % node_path)

            # Retrieve audit file

            # audit_url = get_url_with_credentials(output_storage_settings,
            #     output_prefix + os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=False)
            audit_url = get_url_with_credentials(all_settings, os.path.join(node_path, "audit.txt"), is_relative_path=False)
            audit_content = storage.get_file(audit_url)
            logger.debug('audit_url=%s' % audit_url)

            # extract the best criterion error
            # FIXME: audit.txt is potentially debug file so format may not be fixed.
            p = re.compile("Run (\d+) preserved \(error[ \t]*([0-9\.]+)\)", re.MULTILINE)
            m = p.search(audit_content)
            criterion = None
            if m:
                criterion = float(m.group(2))
                best_numb = int(m.group(1))
                # NB: assumes that subdirss in new input_x will have same names as output dir that created it.
                best_node = input_dir
            else:
                message = "Cannot extract criterion from audit file for iteration %s" % (self.id + 1)
                logger.warn(message)
                raise IOError(message)

            if criterion < min_crit:
                min_crit = criterion
                min_crit_index = best_numb
                min_crit_node = best_node

        logger.debug("min_crit = %s at %s" % (min_crit, min_crit_index))

        if min_crit_index >= sys.maxint:
            raise BadInputException("Unable to find minimum criterion of input files")

        # get previous best criterion
        try:
            self.prev_criterion = float(getval(run_settings, '%s/converge/criterion' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % best_numb)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("min_crit = %f" % min_crit)
        logger.debug('Current min criterion: %f, Prev '
                     'criterion: %f' % (min_crit, self.prev_criterion))
        difference = self.prev_criterion - min_crit
        logger.debug("Difference %f" % difference)

        try:
            max_iteration = int(getval(run_settings, '%s/input/hrmc/max_iteration' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            raise BadInputException("unknown max_iteration")
        logger.debug("max_iteration=%s" % max_iteration)

        try:
            self.error_threshold = float(getval(run_settings, '%s/input/hrmc/error_threshold' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            raise BadInputException("uknown error threshold")
        logger.debug("error_threshold=%s" % self.error_threshold)

        if self.id >= (max_iteration - 1):
            logger.debug("Max Iteration Reached %d " % self.id)
            return (True, min_crit)

        elif min_crit <= self.prev_criterion and difference <= self.error_threshold:
            logger.debug("Convergence reached %f" % difference)
            return (True, min_crit)

        else:
            if difference < 0:
                logger.debug("iteration diverged")
            logger.debug("iteration continues: %d iteration so far" % self.id)

        return (False, min_crit)
