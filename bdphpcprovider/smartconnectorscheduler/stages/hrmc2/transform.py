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
import ast
import json
import logging
from collections import namedtuple
import fnmatch

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import platform
from bdphpcprovider.smartconnectorscheduler import models

from bdphpcprovider.platform import manage
from bdphpcprovider import storage
from bdphpcprovider import mytardis

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

# TODO: key task here is to seperate the domain specific  parts from the
# general parts of this stage and move to different class/module


class Transform(Stage):
    """
        Convert output into input for next iteration.
    """
    # FIXME: put part of config file, or pull from original input file
    domain_input_files = ['input_bo.dat', 'input_gr.dat', 'input_sq.dat']

    def __init__(self, user_settings=None):

        logger.debug("creating transform")
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        pass

    def triggered(self, run_settings):
        try:
            reschedule_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'procs_2b_rescheduled']
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
            logger.debug('self.procs_2b_rescheduled=%s' % self.procs_2b_rescheduled)
            if self.procs_2b_rescheduled:
                return False
        except KeyError, e:
            logger.debug(e)

        try:
            current_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
                    'http://rmit.edu.au/schemas/stages/schedule/current_processes'))
            executed_not_running = [x for x in current_processes if x['status'] == 'ready']
            if executed_not_running:
                logger.debug('executed_not_running=%s' % executed_not_running)
                return False
            else:
                logger.debug('No ready: executed_not_running=%s' % executed_not_running)
        except KeyError, e:
            logger.debug(e)

        try:
            failed_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'failed_nodes']
            failed_nodes = ast.literal_eval(failed_str)
            created_str = run_settings['http://rmit.edu.au/schemas/stages/create'][u'created_nodes']
            created_nodes = ast.literal_eval(created_str)
            if len(failed_nodes) == len(created_nodes) or len(created_nodes) == 0:
                return False
        except KeyError, e:
            logger.debug(e)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/hrmc', u'threshold'):
            # FIXME: need to validate this output to make sure list of int
            self.threshold = ast.literal_eval(run_settings['http://rmit.edu.au/schemas/input/hrmc'][u'threshold'])
        else:
            logger.warn("no threshold found when expected")
            return False
        logger.debug("threshold = %s" % self.threshold)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge', u'converged'):
            # FIXME: should use NUMERIC for bools, so use 0,1 and natural comparison will work.
            self.converged = int(run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'])
        else:
            self.converged = 0

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
            self.runs_left = run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left']
            if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
                self.transformed = int(run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'])
            else:
                self.transformed = 0
            if (self.runs_left == 0) and (not self.transformed) and (not self.converged):
                return True
            else:
                logger.debug("%s %s %s" % (self.runs_left, self.transformed, self.converged))
                pass

        return False

    def copy_files_with_pattern(self, fsys, source_path,
                             dest_path, pattern, output_storage_settings):
        """
        """
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        logger.debug('source_path=%s, dest_path=%s' % (source_path, dest_path))
        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_prefix + source_path)
        _, fnames = fsys.listdir(mypath)
        for f in fnames:
            if fnmatch.fnmatch(f, pattern):
                source_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix + os.path.join(source_path, f), is_relative_path=False)
                dest_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix + os.path.join(dest_path, f), is_relative_path=False)
                logger.debug('source_url=%s, dest_url=%s' % (source_url, dest_url))
                content = storage.get_file(source_url)
                storage.put_file(dest_url, content)

    def retrieve_local_settings(self, run_settings):
        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
          'http://rmit.edu.au/schemas/stages/create/created_nodes')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/max_seed_int')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/compile_file')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/retry_attempts')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/input/system/cloud/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/input/hrmc/threshold')
        self.boto_settings['bdp_username'] = run_settings[
            RMIT_SCHEMA + '/bdp_userprofile']['username']

        logger.debug("boto_settings=%s" % self.boto_settings)

    def process(self, run_settings):

        self.retrieve_local_settings(run_settings)
        #TODO: break up this function as it is way too long
        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']
        bdp_username = self.boto_settings['bdp_username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system'][u'id']
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output_%s" % self.id))
            self.input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % self.id))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % (self.id + 1)))
        else:
            # FIXME: Not clear that this a valid path through stages
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output"))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "input"))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_1"))

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/mytardis', u'experiment_id'):
            try:
                self.experiment_id = int(run_settings['http://rmit.edu.au/schemas/input/mytardis'][u'experiment_id'])
            except ValueError:
                self.experiment_id = 0
        else:
            self.experiment_id = 0
        logger.debug('self.output_dir=%s' % self.output_dir)
        # import time
        # start_time = time.time()
        # logger.debug("Start time %f "% start_time)

        logger.debug("output_storage_settings=%s" % output_storage_settings)
        output_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
            output_prefix + self.output_dir, is_relative_path=False)

        logger.debug("output_url=%s" % output_url)
        # Should this be output_dir or root of remotesys?
        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        fsys = storage.get_filesystem(output_url)
        logger.debug("fsys=%s" % fsys)
        logger.debug("mypath=%s" % mypath)

        node_output_dirs, _ = fsys.listdir(mypath)
        logger.debug("node_output_dirs=%s" % node_output_dirs)
        self.audit = ""
        outputs = []

        Node_info = namedtuple('Node_info',
            ['dir', 'index', 'number', 'criterion'])

        # gather node_infos
        for node_output_dir in node_output_dirs:
            base_fname = "HRMC.inp"
            try:
                values_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(self.output_dir, node_output_dir,
                    '%s_values' % base_fname), is_relative_path=False)
                values_content = storage.get_file(values_url)
                logger.debug("values_file=%s" % values_url)
            except IOError:
                logger.warn("no values file found")
                values_map = {}
            else:
                values_map = dict(json.loads(values_content))
            criterion = self.compute_psd_criterion(
                node_output_dir, fsys,
                output_storage_settings)
            #criterion = self.compute_hrmc_criterion(values_map['run_counter'], node_output_dir, fs,)
            logger.debug("criterion=%s" % criterion)
            index = 0   # FIXME: as node_output_dirs in particular order, then index is not useful.
            outputs.append(Node_info(dir=node_output_dir,
                index=index, number=values_map['run_counter'], criterion=criterion))

        outputs.sort(key=lambda x: int(x.criterion))
        logger.debug("outputs=%s" % outputs)

        mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
        mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

        if mytardis_settings['mytardis_host']:
            for i, node_output_dir in enumerate(node_output_dirs):
                crit = None  # is there an infinity criterion
                for ni in outputs:
                    if ni.dir == node_output_dir:
                        crit = ni.criterion
                        break
                else:
                    logger.debug("criterion not found")
                    continue
                logger.debug("crit=%s" % crit)
                source_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(self.output_dir, node_output_dir),
                    is_relative_path=False)
                logger.debug("source_url=%s" % source_url)
                graph_params = []

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

                #TODO: hrmcexp graph should be tagged to input directories (not output directories)
                #because we want the result after pruning.
                #todo: replace self.boto_setttings with mytardis_settings
                all_settings = dict(self.boto_settings)
                all_settings.update(mytardis_settings)
                all_settings.update(output_storage_settings)

                EXP_DATASET_NAME_SPLIT = 2

                def get_exp_name_for_output(settings, url, path):
                    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

                def get_dataset_name_for_output(settings, url, path):
                    logger.debug("path=%s" % path)

                    host = settings['host']
                    prefix = 'ssh://%s@%s' % (settings['type'], host)

                    source_url = smartconnector.get_url_with_pkey(
                        settings, os.path.join(prefix, path, "HRMC.inp_values"),
                        is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)
                    try:
                        content = storage.get_file(source_url)
                    except IOError, e:
                        logger.warn("cannot read file %s" %e)
                        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    logger.debug("content=%s" % content)
                    try:
                        values_map = dict(json.loads(str(content)))
                    except Exception, e:
                        logger.warn("cannot load %s: %s" % (content, e))
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

                logger.debug('all_settings=%s' % all_settings)
                logger.debug('output_storage_settings=%s' % output_storage_settings)
                self.experiment_id = mytardis.create_dataset(
                    settings=all_settings,
                    source_url=source_url,
                    exp_id=self.experiment_id,
                    exp_name=get_exp_name_for_output,
                    dataset_name=get_dataset_name_for_output,
                    dataset_paramset=[
                        mytardis.create_paramset("hrmcdataset/output", []),
                        mytardis.create_graph_paramset("dsetgraph",
                            name="hrmcdset",
                            graph_info={"axes":["r (Angstroms)", "PSD"],
                                "legends":["psd", "PSD_exp"], "type":"line"},
                            value_dict={"hrmcdset/it": self.id,
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

                        ],
                   datafile_paramset=[
                        mytardis.create_graph_paramset("dfilegraph",
                            name="hrmcdfile",
                            graph_info={},
                            value_dict={},
                            value_keys=[])
                        ],
                   # TODO: move extract function into paramset structure
                   dfile_extract_func={'psd.dat': extract_psd_func,
                        'PSD_exp.dat': extract_psdexp_func,
                        'data_grfinal.dat': extract_grfinal_func,
                        'input_gr.dat': extract_inputgr_func}

                   )
        else:
            logger.warn("no mytardis host specified")
        logger.debug('threshold=%s' % self.threshold)
        total_picks = 1
        if len(self.threshold) > 1:
            for i in self.threshold:
                total_picks *= self.threshold[i]
        else:
            total_picks = self.threshold[0]

        if not outputs:
            logger.error("no ouput found for this iteration")
            return

        for index in range(0, total_picks):
            Node_info = outputs[index]
            logger.debug("node_info.dir=%s" % Node_info.dir)
            logger.debug("Node_info=%s" % str(Node_info))
            self.new_input_node_dir = os.path.join(self.new_input_dir,
                Node_info.dir)
            logger.debug("New input node dir %s" % self.new_input_node_dir)

            # Move all existing domain input files unchanged to next input directory
            for f in self.domain_input_files:
                source_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(self.output_dir, Node_info.dir, f), is_relative_path=False)
                dest_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(self.new_input_node_dir, f),
                    is_relative_path=False)
                logger.debug('source_url=%s, dest_url=%s' % (source_url, dest_url))

                content = storage.get_file(source_url)
                logger.debug('content collected')
                storage.put_file(dest_url, content)
                logger.debug('put successfully')

            logger.debug('put file successfully')
            pattern = "*_values"
            self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
                self.new_input_node_dir, pattern,
                output_storage_settings)

            pattern = "*_template"
            self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
                self.new_input_node_dir, pattern,
                output_storage_settings)

            # NB: Converge stage triggers based on criterion value from audit.

            info = "Run %s preserved (error %s)\n" % (Node_info.number, Node_info.criterion)
            audit_url = smartconnector.get_url_with_pkey(
                output_storage_settings,
                    output_prefix + os.path.join(self.new_input_node_dir, 'audit.txt'), is_relative_path=False)
            storage.put_file(audit_url, info)
            logger.debug("audit=%s" % info)
            self.audit += info

            # move xyz_final.xyz to initial.xyz
            source_url = smartconnector.get_url_with_pkey(
                output_storage_settings,
                output_prefix + os.path.join(self.output_dir, Node_info.dir, "xyz_final.xyz"), is_relative_path=False)
            dest_url = smartconnector.get_url_with_pkey(
                output_storage_settings,
                output_prefix + os.path.join(self.new_input_node_dir, 'input_initial.xyz'), is_relative_path=False)
            content = storage.get_file(source_url)
            storage.put_file(dest_url, content)
            self.audit += "spawning diamond runs\n"

        audit_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
                        output_prefix + os.path.join(self.new_input_dir, 'audit.txt'), is_relative_path=False)
        storage.put_file(audit_url, self.audit)

    def output(self, run_settings):
        logger.debug("transform.output")
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform'):
            run_settings['http://rmit.edu.au/schemas/stages/transform'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'] = 1
        run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] = str(self.experiment_id)

        print "End of Transformation: \n %s" % self.audit

        return run_settings

    def compute_hrmc_criterion(self, number, node_output_dir, fs, output_storage_settings):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        grerr_file = 'grerr%s.dat' % str(number).zfill(2)
        logger.debug("grerr_file=%s " % grerr_file)
        grerr_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
                        output_prefix + os.path.join(self.output_dir,
                            node_output_dir, 'grerr%s.dat' % str(number).zfill(2)), is_relative_path=False)
        grerr_content = storage.get_file(grerr_url)  # FIXME: check that get_file can raise IOError
        if not grerr_content:
            logger.warn("no gerr content found")
        logger.debug("grerr_content=%s" % grerr_content)
        try:
            criterion = float(grerr_content.strip().split('\n')[-1]
            .split()[1])
        except ValueError as e:
            logger.warn("invalid criteron found in grerr "
                        + "file for  %s/%s: %s"
                        % (self.output_dir, node_output_dir, e))
        logger.debug("criterion=%s" % criterion)
        return criterion

    def compute_psd_criterion(self, node_output_dir, fs, output_storage_settings):
        import math
        import os
        #globalFileSystem = fs.get_global_filesystem()
        # psd = os.path.join(globalFileSystem,
        #                    self.output_dir, node_output_dir,
        #                    "PSD_output/psd.dat")
        #Fixme replace all reference to files by parameters, e.g PSDCode
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        logger.debug('compute psd---')
        psd_url = smartconnector.get_url_with_pkey(output_storage_settings,
                        output_prefix + os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "psd.dat"), is_relative_path=False)
        logger.debug('psd_url=%s' % psd_url)

        psd = storage.get_filep(psd_url)
        logger.debug('psd=%s' % psd._name)

        # psd_exp = os.path.join(globalFileSystem,
        #                        self.output_dir, node_output_dir,
        #                        "PSD_output/PSD_exp.dat")
        psd_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
                        output_prefix + os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "PSD_exp.dat"), is_relative_path=False)
        logger.debug('psd_url=%s' % psd_url)
        psd_exp = storage.get_filep(psd_url)
        logger.debug('psd_exp=%s' % psd_exp._name)

        logger.debug("PSD %s %s " % (psd._name, psd_exp._name))
        x_axis = []
        y1_axis = []
        for line in psd:
            column = line.split()
            #logger.debug(column)
            if len(column) > 0:
                x_axis.append(float(column[0]))
                y1_axis.append(float(column[1]))
        logger.debug("x_axis \n %s" % x_axis)
        logger.debug("y1_axis \n %s" % y1_axis)

        y2_axis = []
        for line in psd_exp:
            column = line.split()
            #logger.debug(column)
            if len(column) > 0:
                y2_axis.append(float(column[1]))

        for i in range(len(x_axis) - len(y2_axis)):
            y2_axis.append(0)
        logger.debug("y2_axis \n %s" % y2_axis)

        criterion = 0
        for i in range(len(y1_axis)):
            criterion += math.pow((y1_axis[i] - y2_axis[i]), 2)
        logger.debug("Criterion %f" % criterion)

        criterion_url = smartconnector.get_url_with_pkey(
            output_storage_settings,
            output_prefix + os.path.join(self.output_dir, node_output_dir, "PSD_output", "criterion.txt"),
            is_relative_path=False)
        storage.put_file(criterion_url, str(criterion))

        return criterion



