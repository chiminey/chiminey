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
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


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
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'threshold'):
            # FIXME: need to validate this output to make sure list of int
            self.threshold = ast.literal_eval(run_settings['http://rmit.edu.au/schemas/hrmc'][u'threshold'])
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
                             dest_path, pattern):
        """
        """
        (scheme, host, mypath, location, query_settings) = hrmcstages.parse_bdpurl(source_path)
        _, fnames = fsys.listdir(mypath)
        for f in fnames:
            if fnmatch.fnmatch(f, pattern):
                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(source_path, f), is_relative_path=False)
                dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(dest_path, f), is_relative_path=False)
                content = hrmcstages.get_file(source_url)
                hrmcstages.put_file(dest_url, content)

    # def copy_file(self, fsys, source_path, dest_path):
    #     """
    #     """
    #     logger.debug("source_path=%s" % source_path)
    #     logger.debug("dest_path=%s" % dest_path)
    #     _, fnames = fsys.listdir(source_path)
    #     logger.debug("fnames=%s" % fnames)
    #     for f in fnames:
    #             source_url = smartconnector.get_url_with_pkey(self.boto_settings,
    #                 os.path.join(source_path, f), is_relative_path=True)
    #             dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
    #                 os.path.join(dest_path, f), is_relative_path=True)
    #             content = hrmcstages.get_file(source_url)
    #             hrmcstages.put_file(dest_url, content)

    def process(self, run_settings):
        #TODO: break up this function as it is way too long

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        #TODO: we assume relative path BDP_URL here, but could be made to work with non-relative (ie., remote paths)
        self.job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output_%s" % self.id))
            self.input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % self.id))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % (self.id + 1)))
        else:
            # FIXME: Not clear that this a valid path through stages
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output"))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "input"))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_1"))

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'experiment_id'):
            try:
                self.experiment_id = int(run_settings['http://rmit.edu.au/schemas/hrmc'][u'experiment_id'])
            except ValueError:
                self.experiment_id = 0
        else:
            self.experiment_id = 0
        # import time
        # start_time = time.time()
        # logger.debug("Start time %f "% start_time)
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

        logger.debug("boto_settings=%s" % self.boto_settings)

        output_url = smartconnector.get_url_with_pkey(self.boto_settings,
            self.output_dir, is_relative_path=False)
        logger.debug("output_url=%s" % output_url)
        # Should this be output_dir or root of remotesys?
        (scheme, host, mypath, location, query_settings) = hrmcstages.parse_bdpurl(output_url)
        fsys = hrmcstages.get_filesystem(output_url)
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
                values_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.output_dir, node_output_dir,
                    '%s_values' % base_fname), is_relative_path=False)
                values_content = hrmcstages.get_file(values_url)
                logger.debug("values_file=%s" % values_url)
            except IOError:
                logger.warn("no values file found")
            values_map = dict(json.loads(values_content))
            criterion = self.compute_psd_criterion(node_output_dir, fsys)
            #criterion = self.compute_hrmc_criterion(values_map['run_counter'], node_output_dir, fs)
            logger.debug("criterion=%s" % criterion)
            index = 0   # FIXME: as node_output_dirs in particular order, then index is not useful.
            outputs.append(Node_info(dir=node_output_dir,
                index=index, number=values_map['run_counter'], criterion=criterion))

        outputs.sort(key=lambda x: int(x.criterion))
        logger.debug("outputs=%s" % outputs)

        if self.boto_settings['mytardis_host']:

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
                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.output_dir, node_output_dir), is_relative_path=False)
                logger.debug("source_url=%s" % source_url)
                graph_params = []
                #TODO: hrmcexp graph should be tagged to input directories (not output directories)
                #because we want the result after pruning.
                self.experiment_id = mytardis.post_dataset(
                    settings=self.boto_settings,
                    source_url=source_url,
                    exp_id=self.experiment_id,
                   exp_name=hrmcstages.get_exp_name_for_output,
                   dataset_name=hrmcstages.get_dataset_name_for_output,
                   dataset_paramset=[{
                       "schema": "http://rmit.edu.au/schemas/hrmcdataset/output",
                       "parameters": [],

                   },
                   {
                        "schema": "http://rmit.edu.au/schemas/dsetgraph",
                        "parameters": [
                        {
                            "name": "graph_info",
                            "string_value": '{}'
                        },
                        {
                            "name": "name",
                            "string_value": 'hrmcdset'
                        },
                        {
                            "name": "value_dict",
                            "string_value": '{"hrmcdset/it": %s, "hrmcdset/crit": %s}' % (self.id, crit)
                        },
                        {
                            "name": "value_keys",
                            "string_value": '[]'
                        },
                        ]
                   }

                   ]
                   )
        else:
            logger.warn("no mytardis host specified")

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
                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.output_dir, Node_info.dir, f), is_relative_path=False)
                dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.new_input_node_dir, f),
                    is_relative_path=False)
                content = hrmcstages.get_file(source_url)
                hrmcstages.put_file(dest_url, content)

            pattern = "*_values"
            self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
                self.new_input_node_dir, pattern)

            pattern = "*_template"
            self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
                self.new_input_node_dir, pattern)

            # NB: Converge stage triggers based on criterion value from audit.

            info = "Run %s preserved (error %s)\n" % (Node_info.number, Node_info.criterion)
            audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.new_input_node_dir, 'audit.txt'), is_relative_path=False)
            hrmcstages.put_file(audit_url, info)
            logger.debug("audit=%s" % info)
            self.audit += info

            # move xyz_final.xyz to initial.xyz
            source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                os.path.join(self.output_dir, Node_info.dir, "xyz_final.xyz"), is_relative_path=False)
            dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                os.path.join(self.new_input_node_dir, 'input_initial.xyz'), is_relative_path=False)
            content = hrmcstages.get_file(source_url)
            hrmcstages.put_file(dest_url, content)
            self.audit += "spawning diamond runs\n"



    def output(self, run_settings):
        logger.debug("transform.output")
        audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.new_input_dir, 'audit.txt'), is_relative_path=False)
        hrmcstages.put_file(audit_url, self.audit)

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform'):
            run_settings['http://rmit.edu.au/schemas/stages/transform'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'] = 1
        run_settings['http://rmit.edu.au/schemas/hrmc']['experiment_id'] = str(self.experiment_id)

        print "End of Transformation: \n %s" % self.audit

        return run_settings

    def compute_hrmc_criterion(self, number, node_output_dir, fs):
        grerr_file = 'grerr%s.dat' % str(number).zfill(2)
        logger.debug("grerr_file=%s " % grerr_file)
        grerr_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, 'grerr%s.dat' % str(number).zfill(2)), is_relative_path=False)
        grerr_content = hrmcstages.get_file(grerr_url)  # FIXME: check that get_file can raise IOError
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

    def compute_psd_criterion(self, node_output_dir, fs):
        import math
        import os
        #globalFileSystem = fs.get_global_filesystem()
        # psd = os.path.join(globalFileSystem,
        #                    self.output_dir, node_output_dir,
        #                    "PSD_output/psd.dat")
        #Fixme replace all reference to files by parameters, e.g PSDCode
        psd_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "psd.dat"), is_relative_path=False)
        psd = hrmcstages.get_filep(psd_url)

        # psd_exp = os.path.join(globalFileSystem,
        #                        self.output_dir, node_output_dir,
        #                        "PSD_output/PSD_exp.dat")
        psd_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "PSD_exp.dat"), is_relative_path=False)
        psd_exp = hrmcstages.get_filep(psd_url)

        logger.debug("PSD %s %s " % (psd, psd_exp))
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

        criterion_url = smartconnector.get_url_with_pkey(self.boto_settings,
            os.path.join(self.output_dir, node_output_dir, "PSD_output", "criterion.txt"), is_relative_path=False)
        hrmcstages.put_file(criterion_url, str(criterion))

        # criterion_file = DataObject('criterion.txt')
        # criterion_file.create(str(criterion))
        # criterion_path = os.path.join(self.output_dir,
        #                               node_output_dir, "PSD_output")
        # fs.create(criterion_path, criterion_file)

        return criterion



