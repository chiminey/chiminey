
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
import sys
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages, platform
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider import mytardis
from bdphpcprovider.smartconnectorscheduler import models

logger = logging.getLogger(__name__)

DATA_ERRORS_FILE = "data_errors.dat"
STEP_COLUMN_NUM = 0
ERRGR_COLUMN_NUM = 28

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


# TODO: key task here is to seperate the domain specific  parts from the
# general parts of this stage and move to different class/module

class IterationConverge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, user_settings=None):
        """
        """
        logger.debug("created iteration converge")
        self.total_iterations = 30
        self.number_of_remaining_iterations = 30
        self.id = 0
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number

    def triggered(self, run_settings):
        """
        """
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system'][u'id']
        else:
            logger.warn("Cannot retrieve id. Maybe first iteration?")
            self.id = 0
        logger.debug("id = %s" % self.id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
            self.transformed = int(run_settings['http://rmit.edu.au/schemas/stages/transformed'][u'transformed'])
            return self.transformed
        return False

    def process(self, run_settings):
        """
        """
        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        self.number_of_remaining_iterations -= 1
        print "Number of Iterations Left %d" \
            % self.number_of_remaining_iterations

    def output(self, run_settings):
        """
        """
        if self.number_of_remaining_iterations > 0:
            # trigger first of iteration stages
            logger.debug("nonconvergence")

            # delete_key('runs_left', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['runs_left']

            # delete_key('error_nodes', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['error_nodes']

            #update_key('converged', False, context)
            run_settings['http://rmit.edu.au/stages/converge']['converged'] = False
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge

            # update_key('converged', True, context)
            run_settings['http://rmit.edu.au/stages/converge']['converged'] = True

            # we are done, so don't trigger iteration stages

        #delete_key('transformed', context)
        transform = run_settings['http://rmit.edu.au/schemas/stages/transform']
        del transform['transformed']

        self.id += 1
        #update_key('id', self.id, context)
        run_settings['http://rmit.edu.au/schemas/system'][u'id'] = self.id

        return run_settings


class Converge(Stage):
    """
    Determine whether the function has been optimised
    """
    # TODO: Might be clearer to count up rather than down as id goes up

    def __init__(self, user_settings=None):
        """
        """
        logger.debug("created converge")

        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        self.id = 0

    def triggered(self, run_settings):
        """
        """

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/hrmc', u'error_threshold'):
            self.error_threshold = float(run_settings['http://rmit.edu.au/schemas/input/hrmc'][u'error_threshold'])
            logger.debug("error_threshold=%s" % self.error_threshold)
        else:
            pass  # FIXME: is this an error condition?

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
            self.transformed = int(run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'])
            return self.transformed

        return False

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

    def process(self, run_settings):
        self.retrieve_local_settings(run_settings)
        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']
        bdp_username = self.boto_settings['bdp_username']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = platform.get_platform_settings(output_storage_url, bdp_username)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                      output_storage_settings['type'])
        self.job_dir = platform.get_job_dir(output_storage_settings, run_settings)
        mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
        mytardis_settings = platform.get_platform_settings(mytardis_url, bdp_username)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system'][u'id']
            self.output_dir = os.path.join(self.job_dir, "output_%d" % self.id)
            self.iter_inputdir = os.path.join(self.job_dir, "input_%d" % (self.id + 1))
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = os.path.join(self.job_dir, "output")
            self.iter_inputdir = os.path.join(self.job_dir, "input")
            self.id = 0

        logger.debug('output_dir=%s iter_inputdir=%s' % (self.output_dir, self.iter_inputdir))

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/mytardis', u'experiment_id'):
            try:
                self.experiment_id = int(run_settings['http://rmit.edu.au/schemas/input/mytardis'][u'experiment_id'])
            except ValueError:
                self.experiment_id = 0
        else:
            self.experiment_id = 0

        inputdir_url = smartconnector.get_url_with_pkey(output_storage_settings,
            output_prefix + self.iter_inputdir, is_relative_path=False)
        logger.debug('input_dir_url=%s' % inputdir_url)

        (scheme, host, mypath, location, query_settings) = hrmcstages.parse_bdpurl(inputdir_url)
        fsys = hrmcstages.get_filesystem(inputdir_url)
        logger.debug('mypath=%s' % mypath)
        input_dirs, _ = fsys.listdir(mypath)
        logger.debug('input_dirs=%s' % input_dirs)
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
            # Retrieve audit file

            audit_url = smartconnector.get_url_with_pkey(output_storage_settings,
                output_prefix + os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=False)
            audit_content = hrmcstages.get_file(audit_url)
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

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge', u'criterion'):
            self.prev_criterion = float(run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'])
        else:
            self.prev_criterion = sys.float_info.max - 1.0
            logger.warn("no previous criterion found")

        # check whether we are under the error threshold
        logger.debug("best_num=%s" % best_numb)
        logger.debug("prev_criterion = %f" % self.prev_criterion)
        logger.debug("min_crit = %f" % min_crit)
        self.done_iterating = False

        difference = self.prev_criterion - min_crit
        logger.debug("Difference %f" % difference)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/input/hrmc', u'max_iteration'):
            max_iteration = int(run_settings['http://rmit.edu.au/schemas/input/hrmc'][u'max_iteration'])
        else:
            raise BadInputException("unknown max_iteration")
        logger.debug("max_iteration=%s" % max_iteration)

        if self.id >= (max_iteration - 1):
            logger.debug("Max Iteration Reached %d " % self.id)
            self.done_iterating = True

        elif min_crit <= self.prev_criterion and difference <= self.error_threshold:
            self.done_iterating = True
            logger.debug("Convergence reached %f" % difference)

        else:
            if difference < 0:
                logger.debug("iteration diverged")
            logger.debug("iteration continues: %d iteration so far" % self.id)

        if self.done_iterating:
            logger.debug("Total Iterations: %d" % self.id)
            self._ready_final_output(min_crit_node, min_crit_index, output_storage_settings, mytardis_settings)
            smartconnector.success(run_settings, "%s: finished" % (self.id + 1))

        logger.error('Current min criterion: %f, Prev '
                     'criterion: %f' % (min_crit, self.prev_criterion))

        self.criterion = min_crit

    def _ready_final_output(self, crit_node, crit_index, output_storage_settings, mytardis_settings):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        new_output_dir = os.path.join(self.job_dir,  'output')
        # FIXME: check new_output_dir does not already exist
        #fs.create_local_filesystem(new_output_dir)

        # import shutil, os.path
        # source = os.path.join(fs.get_global_filesystem(), self.output_dir, crit_node)
        # dest = os.path.join(fs.get_global_filesystem(), new_output_dir)
        # logger.debug("Convergence Source %s Destination %s " % (source, dest))
        # shutil.copytree(source, dest)

        source_url = smartconnector.get_url_with_pkey(output_storage_settings,
            output_prefix + os.path.join(self.output_dir), is_relative_path=False)
        dest_url = smartconnector.get_url_with_pkey(output_storage_settings,
            output_prefix + os.path.join(new_output_dir), is_relative_path=False)

        hrmcstages.copy_directories(source_url, dest_url)

        node_dirs = hrmcstages.list_dirs(dest_url)
        logger.debug("node_dirs=%s" % node_dirs)

        if mytardis_settings['mytardis_host']:

            re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

            logger.debug("new_output_dir=%s" % new_output_dir)
            exp_value_keys = []
            legends = []
            for m, node_dir in enumerate(node_dirs):
                exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

                source_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix + os.path.join(new_output_dir, node_dir), is_relative_path=False)

                (source_scheme, source_location, source_path, source_location,
                    query_settings) = hrmcstages.parse_bdpurl(source_url)
                logger.debug("source_url=%s" % source_url)
                legends.append(
                    hrmcstages.get_dataset_name_for_output(
                        output_storage_settings, "", source_path))

            logger.debug("exp_value_keys=%s" % exp_value_keys)
            logger.debug("legends=%s" % legends)

            graph_paramset = [mytardis.create_graph_paramset("expgraph",
                name="hrmcexp2",
                graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
                value_dict={},
                value_keys=exp_value_keys)]

            for m, node_dir in enumerate(node_dirs):

                dataerrors_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix + os.path.join(new_output_dir, node_dir, DATA_ERRORS_FILE), is_relative_path=False)
                dataerrors_content = hrmcstages.get_file(dataerrors_url)
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

                crit_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix + os.path.join(new_output_dir, node_dir, "criterion.txt"), is_relative_path=False)
                try:
                    crit = hrmcstages.get_file(crit_url)
                except ValueError:
                    crit = None
                except IOError:
                    crit = None
                # FIXME: can crit be zero?
                if crit:
                    hrmcdset_val = {"hrmcdset/it": self.id, "hrmcdset/crit": crit}
                else:
                    hrmcdset_val = {}

                source_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(new_output_dir, node_dir), is_relative_path=False)
                logger.debug("source_url=%s" % source_url)

                # TODO: move into utiltiy function for reuse
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
                #todo: replace self.boto_setttings with mytardis_settings
                all_settings = dict(self.boto_settings)
                all_settings.update(mytardis_settings)
                all_settings.update(output_storage_settings)
                self.experiment_id = mytardis.create_dataset(
                    settings=all_settings,
                    source_url=source_url,
                    exp_name=hrmcstages.get_exp_name_for_output,
                    dataset_name=hrmcstages.get_dataset_name_for_output,
                    exp_id=self.experiment_id,
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

    def output(self, run_settings):

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge'):
            run_settings['http://rmit.edu.au/schemas/stages/converge'] = {}

        run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] = str(self.experiment_id)

        if not self.done_iterating:
            # trigger first of iteration stages
            logger.debug("nonconvergence")

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule', {})[u'scheduled_nodes'] = '[]'

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/execute', {})[u'executed_procs'] = '[]'

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'current_processes'] = '[]'

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'total_scheduled_procs'] = 0

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_completed'] = 0

            run_settings.setdefault(
                'http://rmit.edu.au/schemas/stages/schedule',
                {})[u'schedule_started'] = 0

            logger.debug('scheduled_nodes=%s' % run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'scheduled_nodes'])

            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['runs_left']

            # delete_key('error_nodes', context)
            run = run_settings['http://rmit.edu.au/schemas/stages/run']
            del run['error_nodes']

            #update_key('converged', False, context)
            run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'] = 0
            # delete_key('runs_left', context)
            # delete_key('error_nodes', context)
            # update_key('converged', False, context)
        else:
            logger.debug("convergence")
            # we are done, so trigger next stage outside of converge
            #update_key('converged', True, context)
            run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'] = 1
            # we are done, so don't trigger iteration stages

        #update_key('criterion', self.criterion, context)
        run_settings['http://rmit.edu.au/schemas/stages/converge'][u'criterion'] = unicode(self.criterion)
         # delete_key('error_nodes', context)
        #delete_key('transformed', context)
        run = run_settings['http://rmit.edu.au/schemas/stages/transform']
        del run['transformed']

        self.id += 1
        # update_key('id', self.id, context)
        run_settings['http://rmit.edu.au/schemas/system'][u'id'] = self.id

        return run_settings
