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
import ast
import json
import logging
from collections import namedtuple
import fnmatch


from bdphpcprovider.storage import get_url_with_pkey
from bdphpcprovider.runsettings import getval, SettingNotFoundException

from bdphpcprovider import storage
from bdphpcprovider import mytardis
from bdphpcprovider.corestages import Transform


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"
DOMAIN_INPUT_FILES = ['input_bo.dat', 'input_gr.dat', 'input_sq.dat']


class VASPTransform(Transform):

    def curate_dataset(self, run_settings, experiment_id, base_dir, output_url,
        all_settings):

        OUTCAR_FILE = "OUTCAR"
        VALUES_FILE = "values"

        logger.debug("output_url=%s" % output_url)

        outcar_url = storage.get_url_with_pkey(local_settings,
            os.path.join(output_url, OUTCAR_FILE), is_relative_path=False)
        logger.debug("outcar_url=%s" % outcar_url)

        try:
            outcar_content = storage.get_file(outcar_url)
        except IOError, e:
            logger.error(e)
            toten = None
        else:
            toten = None
            for line in outcar_content.split('\n'):
                #logger.debug("line=%s" % line)
                if 'e  en' in line:
                    logger.debug("found")
                    try:
                        toten = float(line.rsplit(' ', 2)[-2])
                    except ValueError, e:
                        logger.error(e)
                        pass
                    break

        logger.debug("toten=%s" % toten)

        values_url = storage.get_url_with_pkey(local_settings,
            os.path.join(output_url, VALUES_FILE), is_relative_path=False)
        logger.debug("values_url=%s" % values_url)
        try:
            values_content = storage.get_file(values_url)
        except IOError, e:
            logger.error(e)
            values = None
        else:
            values = None
            try:
                values = dict(json.loads(values_content))
            except Exception, e:
                logger.error(e)
                pass
        logger.debug("values=%s" % values)

        # FIXME: all values from map are strings initially, so need to know
        # type to coerce.
        num_kp = None
        if 'num_kp' in values:
            try:
                num_kp = int(values['num_kp'])
            except IndexError:
                pass
            except ValueError:
                pass

        logger.debug("num_kp=%s" % num_kp)

        encut = None
        if 'encut' in values:
            try:
                encut = int(values['encut'])
            except IndexError:
                pass
            except ValueError:
                pass
        logger.debug("encut=%s" % encut)

        def _get_exp_name_for_vasp(settings, url, path):
            """
            Break path based on EXP_DATASET_NAME_SPLIT
            """
            return str(os.sep.join(path.split(os.sep)[-2:-1]))

        def _get_dataset_name_for_vasp(settings, url, path):
            """
            Break path based on EXP_DATASET_NAME_SPLIT
            """
            encut = settings['ENCUT']
            numkp = settings['NUMKP']
            runcounter = settings['RUNCOUNTER']
            return "%s:encut=%s,num_kp=%s" % (runcounter, encut, numkp)
            #return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

        mytardis_settings['ENCUT'] = encut
        mytardis_settings['NUMKP'] = num_kp
        mytardis_settings['RUNCOUNTER'] = local_settings['contextid']

        experiment_id = mytardis.create_dataset(
            settings=mytardis_settings,
            source_url=output_url,
            exp_id=experiment_id,
            exp_name=_get_exp_name_for_vasp,
            dataset_name=_get_dataset_name_for_vasp,
            dataset_paramset=[
                mytardis.create_paramset("remotemake/output", []),
                mytardis.create_graph_paramset("dsetgraph",
                    name="makedset",
                    graph_info={},
                    value_dict={"makedset/num_kp": num_kp, "makedset/encut": encut, "makedset/toten": toten}
                        if (num_kp is not None)
                            and (encut is not None)
                            and (toten is not None) else {},
                    value_keys=[]
                    ),
                ]
            )

        return experiment_id










        # iteration = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        # iter_output_dir = os.path.join(os.path.join(base_dir, "output_%s" % iteration))
        # output_prefix = '%s://%s@' % (all_settings['scheme'],
        #                             all_settings['type'])
        # iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)

        # (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        # fsys = storage.get_filesystem(output_url)

        # node_output_dirnames, _ = fsys.listdir(mypath)
        # logger.debug("node_output_dirnames=%s" % node_output_dirnames)

        # if all_settings['mytardis_host']:
        #     for i, node_output_dirname in enumerate(node_output_dirnames):
        #         node_path = os.path.join(iter_output_dir, node_output_dirname)
        #         # find criterion
        #         crit = None  # is there an infinity criterion
        #         for ni in self.outputs:
        #             if ni.dirname == node_output_dirname:
        #                 crit = ni.criterion
        #                 break
        #         else:
        #             logger.debug("criterion not found")
        #             continue
        #         logger.debug("crit=%s" % crit)

        #         # graph_params = []

        #         def extract_psd_func(fp):
        #             res = []
        #             xs = []
        #             ys = []
        #             for i, line in enumerate(fp):
        #                 columns = line.split()
        #                 xs.append(float(columns[0]))
        #                 ys.append(float(columns[1]))
        #             res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
        #             return res

        #         def extract_psdexp_func(fp):
        #             res = []
        #             xs = []
        #             ys = []
        #             for i, line in enumerate(fp):
        #                 columns = line.split()
        #                 xs.append(float(columns[0]))
        #                 ys.append(float(columns[1]))
        #             res = {"hrmcdfile/r2": xs, "hrmcdfile/g2": ys}
        #             return res

        #         def extract_grfinal_func(fp):
        #             res = []
        #             xs = []
        #             ys = []
        #             for i, line in enumerate(fp):
        #                 columns = line.split()
        #                 xs.append(float(columns[0]))
        #                 ys.append(float(columns[1]))
        #             #FIXME: len(xs) == len(ys) for this to work.
        #             #TODO: hack to handle when xs and ys are too
        #             # large to fit in Parameter with db_index.
        #             # solved by function call at destination
        #             cut_xs = [xs[i] for i, x in enumerate(xs)
        #                 if (i % (len(xs) / 20) == 0)]
        #             cut_ys = [ys[i] for i, x in enumerate(ys)
        #                 if (i % (len(ys) / 20) == 0)]

        #             res = {"hrmcdfile/r3": cut_xs, "hrmcdfile/g3": cut_ys}
        #             return res

        #         def extract_inputgr_func(fp):
        #             res = []
        #             xs = []
        #             ys = []
        #             for i, line in enumerate(fp):
        #                 columns = line.split()
        #                 xs.append(float(columns[0]))
        #                 ys.append(float(columns[1]))
        #             #FIXME: len(xs) == len(ys) for this to work.
        #             #TODO: hack to handle when xs and ys are too
        #             # large to fit in Parameter with db_index.
        #             # solved by function call at destination
        #             cut_xs = [xs[i] for i, x in enumerate(xs)
        #                 if (i % (len(xs) / 20) == 0)]
        #             cut_ys = [ys[i] for i, x in enumerate(ys)
        #                 if (i % (len(ys) / 20) == 0)]

        #             res = {"hrmcdfile/r4": cut_xs, "hrmcdfile/g4": cut_ys}
        #             return res

        #         #TODO: hrmcexp graph should be tagged to input directories (not output directories)
        #         #because we want the result after pruning.
        #         #todo: replace self.boto_setttings with mytardis_settings

        #         EXP_DATASET_NAME_SPLIT = 2

        #         def get_exp_name_for_output(settings, url, path):
        #             # return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))
        #             return str(os.sep.join(path.split(os.sep)[-4:-2]))

        #         def get_dataset_name_for_output(settings, url, path):
        #             logger.debug("path=%s" % path)

        #             host = settings['host']
        #             prefix = 'ssh://%s@%s' % (settings['type'], host)

        #             source_url = get_url_with_pkey(
        #                 settings, os.path.join(prefix, path, "HRMC.inp_values"),
        #                 is_relative_path=False)
        #             logger.debug("source_url=%s" % source_url)
        #             try:
        #                 content = storage.get_file(source_url)
        #             except IOError, e:
        #                 logger.warn("cannot read file %s" % e)
        #                 return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

        #             logger.debug("content=%s" % content)
        #             try:
        #                 values_map = dict(json.loads(str(content)))
        #             except Exception, e:
        #                 logger.warn("cannot load %s: %s" % (content, e))
        #                 return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

        #             try:
        #                 iteration = str(path.split(os.sep)[-2:-1][0])
        #             except Exception, e:
        #                 logger.error(e)
        #                 iteration = ""

        #             if "_" in iteration:
        #                 iteration = iteration.split("_")[1]
        #             else:
        #                 iteration = "final"

        #             dataset_name = "%s_%s_%s" % (iteration,
        #                 values_map['generator_counter'],
        #                 values_map['run_counter'])
        #             logger.debug("dataset_name=%s" % dataset_name)
        #             return dataset_name

        #         source_dir_url = get_url_with_pkey(
        #             all_settings,
        #             node_path,
        #             is_relative_path=False)
        #         logger.debug("source_dir_url=%s" % source_dir_url)
        #         logger.debug('all_settings=%s' % all_settings)
        #         experiment_id = mytardis.create_dataset(
        #             settings=all_settings,
        #             source_url=source_dir_url,
        #             exp_id=experiment_id,
        #             exp_name=get_exp_name_for_output,
        #             dataset_name=get_dataset_name_for_output,
        #             dataset_paramset=[
        #                 mytardis.create_paramset("hrmcdataset/output", []),
        #                 mytardis.create_graph_paramset("dsetgraph",
        #                     name="hrmcdset",
        #                     graph_info={"axes":["r (Angstroms)", "PSD"],
        #                         "legends":["psd", "PSD_exp"], "type":"line"},
        #                     value_dict={"hrmcdset/it": self.id,
        #                          "hrmcdset/crit": crit},
        #                     value_keys=[["hrmcdfile/r1", "hrmcdfile/g1"],
        #                         ["hrmcdfile/r2", "hrmcdfile/g2"]]
        #                     ),
        #                 mytardis.create_graph_paramset("dsetgraph",
        #                     name="hrmcdset2",
        #                     graph_info={"axes":["r (Angstroms)", "g(r)"],
        #                         "legends":["data_grfinal", "input_gr"],
        #                         "type":"line"},
        #                     value_dict={},
        #                     value_keys=[["hrmcdfile/r3", "hrmcdfile/g3"],
        #                         ["hrmcdfile/r4", "hrmcdfile/g4"]]
        #                     ),

        #                 ],
        #            datafile_paramset=[
        #                 mytardis.create_graph_paramset("dfilegraph",
        #                     name="hrmcdfile",
        #                     graph_info={},
        #                     value_dict={},
        #                     value_keys=[])
        #                 ],
        #            # TODO: move extract function into paramset structure
        #            dfile_extract_func={'psd.dat': extract_psd_func,
        #                 'PSD_exp.dat': extract_psdexp_func,
        #                 'data_grfinal.dat': extract_grfinal_func,
        #                 'input_gr.dat': extract_inputgr_func}

        #            )
        # else:
        #     logger.warn("no mytardis host specified")
        #     return 0
        # return experiment_id
