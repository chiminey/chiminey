
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
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)

DATA_ERRORS_FILE = "data_errors.dat"
STEP_COLUMN_NUM = 0
ERRGR_COLUMN_NUM = 28



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
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
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
        run_settings['http://rmit.edu.au/schemas/system/misc'][u'id'] = self.id

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
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'error_threshold'):
            self.error_threshold = float(run_settings['http://rmit.edu.au/schemas/hrmc'][u'error_threshold'])
        else:
            pass  # FIXME: is this an error condition?

        logger.debug("error_threshold=%s" % self.error_threshold)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
            self.transformed = int(run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'])
            return self.transformed

        return False

    def process(self, run_settings):

        #import time
        # start_time = time.time()
        # logger.debug("Start time %f "% start_time)

        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        #TODO: we assume relative path BDP_URL here, but could be made to work with non-relative (ie., remote paths)
        self.job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.output_dir = os.path.join(self.job_dir, "output_%d" % self.id)
            self.iter_inputdir = os.path.join(self.job_dir, "input_%d" % (self.id + 1))
            #self.new_iter_inputdir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = os.path.join(self.job_dir, "output")
            self.iter_inputdir = os.path.join(self.job_dir, "input")
            self.id = 0

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'experiment_id'):
            try:
                self.experiment_id = int(run_settings['http://rmit.edu.au/schemas/hrmc'][u'experiment_id'])
            except ValueError, e:
                self.experiment_id = 0
        else:
            self.experiment_id = 0

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
            'http://rmit.edu.au/schemas/hrmc/max_seed_int')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/compile_file')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/retry_attempts')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')
        self.boto_settings['username'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['username'] = 'root'  # FIXME: schema value is ignored
        self.boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']

        key_file = hrmcstages.retrieve_private_key(self.boto_settings,
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nectar_private_key'])

        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file

        inputdir_url = smartconnector.get_url_with_pkey(self.boto_settings,
            self.iter_inputdir, is_relative_path=False)
        (scheme, host, mypath, location, query_settings) = hrmcstages.parse_bdpurl(inputdir_url)
        fsys = hrmcstages.get_filesystem(inputdir_url)
        input_dirs, _ = fsys.listdir(mypath)
        # TODO: store all audit info in single file in input_X directory in transform,
        # so we do not have to load individual files within node directories here.
        min_crit = sys.float_info.max - 1.0
        min_crit_index = sys.maxint

        # # retrive the audit file for last iteration
        # fs = get_filesys(context)

        # self.settings = get_all_settings(context)
        # logger.debug("settings = %s" % self.settings)

        # logger.debug("input dir %s" % self.iter_inputdir)
        # input_dirs = fs.get_local_subdirectories(self.iter_inputdir)
        # logger.debug("input_dirs = %s" % input_dirs)

        # # TODO: store all audit info in single file in input_X directory in transform,
        # # so we do not have to load individual files within node directories here.
        # min_crit = sys.float_info.max - 1.0
        # min_crit_index = sys.maxint
        logger.debug("input_dirs=%s" % input_dirs)
        for input_dir in input_dirs:
            # Retrieve audit file

            audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                os.path.join(self.iter_inputdir, input_dir, 'audit.txt'), is_relative_path=False)
            audit_content = hrmcstages.get_file(audit_url)

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

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'max_iteration'):
            max_iteration = int(run_settings['http://rmit.edu.au/schemas/hrmc'][u'max_iteration'])
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
            self._ready_final_output(min_crit_node, min_crit_index)

        logger.error('Current min criterion: %f, Prev '
                     'criterion: %f' % (min_crit, self.prev_criterion))

        self.criterion = min_crit

        # # end_time = time.time()
        # # logger.debug("End time %f "% end_time)

        # try:
        #     converge_vec = self.settings['converge_time']
        # except KeyError:
        #     converge_vec = []

        # converge_vec.append(end_time-start_time)
        # update_key("converge_time", converge_vec, self.settings)

    def _ready_final_output(self, crit_node, crit_index):

        new_output_dir = os.path.join(self.job_dir,  'output')
        # FIXME: check new_output_dir does not already exist
        #fs.create_local_filesystem(new_output_dir)

        # import shutil, os.path
        # source = os.path.join(fs.get_global_filesystem(), self.output_dir, crit_node)
        # dest = os.path.join(fs.get_global_filesystem(), new_output_dir)
        # logger.debug("Convergence Source %s Destination %s " % (source, dest))
        # shutil.copytree(source, dest)

        source_url = smartconnector.get_url_with_pkey(self.boto_settings,
            os.path.join(self.output_dir), is_relative_path=False)
        dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
            os.path.join(new_output_dir), is_relative_path=False)

        hrmcstages.copy_directories(source_url, dest_url)

        node_dirs = hrmcstages.list_dirs(dest_url)
        logger.debug("node_dirs=%s" % node_dirs)

        if self.boto_settings['mytardis_host']:

            re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

            for m, node_dir in enumerate(node_dirs):

                dataerrors_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(new_output_dir, node_dir, DATA_ERRORS_FILE), is_relative_path=False)
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

                crit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(new_output_dir, node_dir, "criterion.txt"), is_relative_path=False)
                try:
                    crit = hrmcstages.get_file(crit_url)
                except ValueError:
                    crit = None
                except IOError:
                    crit = None
                # FIXME: can crit be zero?
                if crit:
                    hrmcdset_val = '{"hrmcdset/it": %s, "hrmcdset/crit": %s}' % (self.id, crit)
                else:
                    hrmcdset_val = '{}'

                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(new_output_dir, node_dir), is_relative_path=False)
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

                self.experiment_id = mytardis.post_dataset(
                    settings=self.boto_settings,
                    source_url=source_url,
                    exp_name=hrmcstages.get_exp_name_for_output,
                    dataset_name=hrmcstages.get_dataset_name_for_output,
                    exp_id=self.experiment_id,
                    dataset_paramset=[{
                        "schema": "http://rmit.edu.au/schemas/hrmcdataset/output",
                        "parameters": [],

                    },
                    {
                         "schema": "http://rmit.edu.au/schemas/dsetgraph",
                         "parameters": [
                         {
                             "name": "graph_info",
                             "string_value": '{"axes":["r (Angstroms)","g(r)"], "legends":["psd", "PSD_exp"],  "type":"line"}'
                         },
                         {
                             "name": "name",
                             "string_value": 'hrmcdset'
                         },
                         {
                             "name": "value_dict",
                             "string_value": hrmcdset_val
                         },
                         {
                             "name": "value_keys",
                             "string_value": '[["hrmcdfile/r1", "hrmcdfile/g1"],["hrmcdfile/r2","hrmcdfile/g2"]]'
                         },
                         ]
                    },
                    {
                         "schema": "http://rmit.edu.au/schemas/dsetgraph",
                         "parameters": [
                         {
                             "name": "graph_info",
                             "string_value": '{"axes":["r (Angstroms)","g(r)"], "legends":["data_grfinal", "input_gr"], "type":"line"}'
                         },
                         {
                             "name": "name",
                             "string_value": 'hrmcdset2'
                         },
                         {
                             "name": "value_dict",
                             "string_value": '{}',
                         },
                         {
                             "name": "value_keys",
                             "string_value": '[["hrmcdfile/r3", "hrmcdfile/g3"],["hrmcdfile/r4","hrmcdfile/g4"]]'
                         },
                         ]
                    },
                    {
                        "schema": "http://rmit.edu.au/schemas/dsetgraph",
                        "parameters": [
                        {
                            "name": "graph_info",
                            "string_value": "{}"
                        },
                        {
                            "name": "name",
                            "string_value": 'hrmcdset%s' % m
                        },
                        {
                        "name": "value_dict",
                        "string_value": '{"hrmcdset%s/step": %s, "hrmcdset%s/err": %s}' % (m, xs, m, ys)
                        },
                        {
                        "name": "value_keys",
                        "string_value": '[]'
                        },
                        ]
                    }],
                    datafile_paramset=[
                    {
                         "schema": "http://rmit.edu.au/schemas/dfilegraph",
                         "parameters": [
                         {
                             "name": "graph_info",
                             "string_value": '{}'
                         },
                         {
                             "name": "name",
                             "string_value": 'hrmcdfile'
                         },
                         {
                             "name": "value_dict",
                             "string_value": '{}'
                         },
                         {
                             "name": "value_keys",
                             "string_value": '[]'
                         },
                         ]
                    },
                    ],
                    # TODO: move extract function into paramset structure
                    dfile_extract_func={'psd.dat': extract_psd_func,
                         'PSD_exp.dat': extract_psdexp_func,
                         'data_grfinal.dat': extract_grfinal_func,
                         'input_gr.dat': extract_inputgr_func}

                    )
        else:
            logger.warn("no mytardis host specified")

    def output(self, run_settings):

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge'):
            run_settings['http://rmit.edu.au/schemas/stages/converge'] = {}

        run_settings['http://rmit.edu.au/schemas/hrmc']['experiment_id'] = str(self.experiment_id)

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
        run_settings['http://rmit.edu.au/schemas/system/misc'][u'id'] = self.id

        return run_settings

