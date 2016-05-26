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
import logging

from chiminey.storage import get_url_with_credentials
from chiminey.corestages.stage import Stage
from chiminey.smartconnectorscheduler import jobs
from chiminey.platform import manage
from chiminey import storage
from chiminey.runsettings import getval, setvals, SettingNotFoundException
from chiminey import messages
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

from django.conf import settings as django_settings

RMIT_SCHEMA = django_settings.SCHEMA_PREFIX

# DOMAIN_INPUT_FILES = ['input_bo.dat', 'input_gr.dat', 'input_sq.dat']


class Transform(Stage):
    """
        Convert output into input for next iteration.
    """
    # FIXME: put part of config file, or pull from original input file

    def __init__(self, user_settings=None):

        logger.debug("creating transform")
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        pass

    def is_triggered(self, run_settings):
        try:
            reschedule_str = getval(
                run_settings,
                '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA)
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
            logger.debug('self.procs_2b_rescheduled=%s' % self.procs_2b_rescheduled)
            if self.procs_2b_rescheduled:
                return False
        except SettingNotFoundException, e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            current_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/current_processes' % RMIT_SCHEMA))
            executed_not_running = [x for x in current_processes if x['status'] == 'ready']
            if executed_not_running:
                logger.debug('executed_not_running=%s' % executed_not_running)
                return False
            else:
                logger.debug('No ready: executed_not_running=%s' % executed_not_running)
        except SettingNotFoundException as e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            failed_str = getval(run_settings, '%s/stages/create/failed_nodes' % RMIT_SCHEMA)
            failed_nodes = ast.literal_eval(failed_str)
            created_str = getval(run_settings, '%s/stages/create/created_nodes' % RMIT_SCHEMA)
            created_nodes = ast.literal_eval(created_str)
            if len(failed_nodes) == len(created_nodes) or len(created_nodes) == 0:
                return False
        except SettingNotFoundException as e:
            logger.debug(e)
        except ValueError as e:
            logger.error(e)

        try:
            self.converged = int(getval(run_settings, '%s/stages/converge/converged' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError) as e:
            self.converged = 0

        try:
            self.runs_left = getval(run_settings, '%s/stages/run/runs_left' % RMIT_SCHEMA)
        except SettingNotFoundException as e:
            pass
        else:
            try:
                self.transformed = int(getval(run_settings, '%s/stages/transform/transformed' % RMIT_SCHEMA))
            except (SettingNotFoundException, ValueError) as e:
                self.transformed = 0
            if (self.runs_left == 0) and (not self.transformed) and (not self.converged):
                return True
            else:
                logger.debug("%s %s %s" % (self.runs_left, self.transformed, self.converged))
                pass

        return False

    def process(self, run_settings):
        try:
            id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            id = 0
        messages.info(run_settings, '%d: transforming' % (id+1))

        # self.contextid = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)
        bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        logger.debug("output_storage_settings=%s" % output_storage_settings)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        offset = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)

        try:
            self.id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output_%s" % self.id))
            self.input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % self.id))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_%d" % (self.id + 1)))
        except (SettingNotFoundException, ValueError):
            # FIXME: Not clear that this a valid path through stages
            self.output_dir = os.path.join(os.path.join(self.job_dir, "output"))
            self.output_dir = os.path.join(os.path.join(self.job_dir, "input"))
            self.new_input_dir = os.path.join(os.path.join(self.job_dir, "input_1"))

        logger.debug('self.output_dir=%s' % self.output_dir)

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        output_url = get_url_with_credentials(
            output_storage_settings,
            output_prefix + self.output_dir, is_relative_path=False)

        # (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        # fsys = storage.get_filesystem(output_url)

        # node_output_dirs, _ = fsys.listdir(mypath)
        # logger.debug("node_output_dirs=%s" % node_output_dirs)

        outputs = self.process_outputs(run_settings, self.job_dir, output_url, output_storage_settings, offset)


        # logger.debug("output_url=%s" % output_url)
        # # Should this be output_dir or root of remotesys?
        # (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        # fsys = storage.get_filesystem(output_url)
        # logger.debug("fsys=%s" % fsys)
        # logger.debug("mypath=%s" % mypath)

        # node_output_dirs, _ = fsys.listdir(mypath)
        # logger.debug("node_output_dirs=%s" % node_output_dirs)
        # self.audit = ""
        # outputs = []

        # Node_info = namedtuple('Node_info',
        #     ['dir', 'index', 'number', 'criterion'])

        # # gather node_infos
        # for node_output_dir in node_output_dirs:
        #     base_fname = "HRMC.inp"
        #     try:
        #         values_url = get_url_with_credentials(
        #             output_storage_settings,
        #             output_prefix + os.path.join(self.output_dir, node_output_dir,
        #             '%s_values' % base_fname), is_relative_path=False)
        #         values_content = storage.get_file(values_url)
        #         logger.debug("values_file=%s" % values_url)
        #     except IOError:
        #         logger.warn("no values file found")
        #         values_map = {}
        #     else:
        #         values_map = dict(json.loads(values_content))
        #     criterion = self.compute_psd_criterion(
        #         node_output_dir, fsys,
        #         output_storage_settings)
        #     #criterion = self.compute_hrmc_criterion(values_map['run_counter'], node_output_dir, fs,)
        #     logger.debug("criterion=%s" % criterion)
        #     index = 0   # FIXME: as node_output_dirs in particular order, then index is not useful.
        #     outputs.append(Node_info(dir=node_output_dir,
        #         index=index, number=values_map['run_counter'], criterion=criterion))

        # outputs.sort(key=lambda x: int(x.criterion))
        # logger.debug("outputs=%s" % outputs)

        # logger.debug('threshold=%s' % self.threshold)
        # total_picks = 1
        # if len(self.threshold) > 1:
        #     for i in self.threshold:
        #         total_picks *= self.threshold[i]
        # else:
        #     total_picks = self.threshold[0]

        # if not outputs:
        #     logger.error("no ouput found for this iteration")
        #     return

        # for index in range(0, total_picks):
        #     Node_info = outputs[index]
        #     logger.debug("node_info.dir=%s" % Node_info.dir)
        #     logger.debug("Node_info=%s" % str(Node_info))
        #     self.new_input_node_dir = os.path.join(self.new_input_dir,
        #         Node_info.dir)
        #     logger.debug("New input node dir %s" % self.new_input_node_dir)

        #     # Move all existing domain input files unchanged to next input directory
        #     for f in self.DOMAIN_INPUT_FILES:
        #         source_url = get_url_with_credentials(
        #             output_storage_settings,
        #             output_prefix + os.path.join(self.output_dir, Node_info.dir, f), is_relative_path=False)
        #         dest_url = get_url_with_credentials(
        #             output_storage_settings,
        #             output_prefix + os.path.join(self.new_input_node_dir, f),
        #             is_relative_path=False)
        #         logger.debug('source_url=%s, dest_url=%s' % (source_url, dest_url))

        #         content = storage.get_file(source_url)
        #         logger.debug('content collected')
        #         storage.put_file(dest_url, content)
        #         logger.debug('put successfully')

        #     logger.debug('put file successfully')
        #     pattern = "*_values"
        #     self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
        #         self.new_input_node_dir, pattern,
        #         output_storage_settings)

        #     pattern = "*_template"
        #     self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, Node_info.dir),
        #         self.new_input_node_dir, pattern,
        #         output_storage_settings)

        #     # NB: Converge stage triggers based on criterion value from audit.

        #     info = "Run %s preserved (error %s)\n" % (Node_info.number, Node_info.criterion)
        #     audit_url = get_url_with_credentials(
        #         output_storage_settings,
        #             output_prefix + os.path.join(self.new_input_node_dir, 'audit.txt'), is_relative_path=False)
        #     storage.put_file(audit_url, info)
        #     logger.debug("audit=%s" % info)
        #     self.audit += info

        #     # move xyz_final.xyz to initial.xyz
        #     source_url = get_url_with_credentials(
        #         output_storage_settings,
        #         output_prefix + os.path.join(self.output_dir, Node_info.dir, "xyz_final.xyz"), is_relative_path=False)
        #     dest_url = get_url_with_credentials(
        #         output_storage_settings,
        #         output_prefix + os.path.join(self.new_input_node_dir, 'input_initial.xyz'), is_relative_path=False)
        #     content = storage.get_file(source_url)
        #     storage.put_file(dest_url, content)
        #     self.audit += "spawning diamond runs\n"

        # audit_url = get_url_with_credentials(
        #     output_storage_settings,
        #                 output_prefix + os.path.join(self.new_input_dir, 'audit.txt'), is_relative_path=False)
        # storage.put_file(audit_url, self.audit)

        # curate dataset into mytardis
        try:
            curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
        except SettingNotFoundException:
            curate_data = 0
        if curate_data:

            mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

            all_settings = dict(mytardis_settings)
            all_settings.update(output_storage_settings)
            all_settings['contextid'] = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)



            try:
                mytardis_platform = jobs.safe_import('chiminey.platform.mytardis.MyTardisPlatform', [], {})
                logger.debug('self_outpus=%s' % outputs)
                self.experiment_id = mytardis_platform.curate_transformed_dataset(run_settings, self.experiment_id, self.job_dir, output_url, all_settings, outputs=outputs)
            except ImproperlyConfigured as  e:
                logger.error("Cannot load mytardis platform hook %s" % e)

        else:
            logger.warn('Data curation is off')


    def output(self, run_settings):
        logger.debug("transform.output")

        # if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform'):
        #     run_settings['http://rmit.edu.au/schemas/stages/transform'] = {}

        setvals(run_settings, {
                '%s/stages/transform/transformed' % RMIT_SCHEMA: 1,
                '%s/input/mytardis/experiment_id' % RMIT_SCHEMA: str(self.experiment_id),
                })
        # run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'] = 1
        # run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] = str(self.experiment_id)

        #print "End of Transformation: \n %s" % self.audit

        return run_settings

    # def compute_hrmc_criterion(self, number, node_output_dir, fs, output_storage_settings):
    #     output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
    #                                 output_storage_settings['type'])
    #     grerr_file = 'grerr%s.dat' % str(number).zfill(2)
    #     logger.debug("grerr_file=%s " % grerr_file)
    #     grerr_url = get_url_with_credentials(
    #         output_storage_settings,
    #                     output_prefix + os.path.join(self.output_dir,
    #                         node_output_dir, 'grerr%s.dat' % str(number).zfill(2)), is_relative_path=False)
    #     grerr_content = storage.get_file(grerr_url)  # FIXME: check that get_file can raise IOError
    #     if not grerr_content:
    #         logger.warn("no gerr content found")
    #     logger.debug("grerr_content=%s" % grerr_content)
    #     try:
    #         criterion = float(grerr_content.strip().split('\n')[-1]
    #         .split()[1])
    #     except ValueError as e:
    #         logger.warn("invalid criteron found in grerr "
    #                     + "file for  %s/%s: %s"
    #                     % (self.output_dir, node_output_dir, e))
    #     logger.debug("criterion=%s" % criterion)
    #     return criterion

    # def compute_psd_criterion(self, node_output_dir, fs, output_storage_settings):
    #     import math
    #     import os
    #     #globalFileSystem = fs.get_global_filesystem()
    #     # psd = os.path.join(globalFileSystem,
    #     #                    self.output_dir, node_output_dir,
    #     #                    "PSD_output/psd.dat")
    #     #Fixme replace all reference to files by parameters, e.g PSDCode
    #     output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
    #                                 output_storage_settings['type'])
    #     logger.debug('compute psd---')
    #     psd_url = get_url_with_credentials(output_storage_settings,
    #                     output_prefix + os.path.join(self.output_dir,
    #                         node_output_dir, "PSD_output", "psd.dat"), is_relative_path=False)
    #     logger.debug('psd_url=%s' % psd_url)

    #     psd = storage.get_filep(psd_url)
    #     logger.debug('psd=%s' % psd._name)

    #     # psd_exp = os.path.join(globalFileSystem,
    #     #                        self.output_dir, node_output_dir,
    #     #                        "PSD_output/PSD_exp.dat")
    #     psd_url = get_url_with_credentials(
    #         output_storage_settings,
    #                     output_prefix + os.path.join(self.output_dir,
    #                         node_output_dir, "PSD_output", "PSD_exp.dat"), is_relative_path=False)
    #     logger.debug('psd_url=%s' % psd_url)
    #     psd_exp = storage.get_filep(psd_url)
    #     logger.debug('psd_exp=%s' % psd_exp._name)

    #     logger.debug("PSD %s %s " % (psd._name, psd_exp._name))
    #     x_axis = []
    #     y1_axis = []
    #     for line in psd:
    #         column = line.split()
    #         #logger.debug(column)
    #         if len(column) > 0:
    #             x_axis.append(float(column[0]))
    #             y1_axis.append(float(column[1]))
    #     logger.debug("x_axis \n %s" % x_axis)
    #     logger.debug("y1_axis \n %s" % y1_axis)

    #     y2_axis = []
    #     for line in psd_exp:
    #         column = line.split()
    #         #logger.debug(column)
    #         if len(column) > 0:
    #             y2_axis.append(float(column[1]))

    #     for i in range(len(x_axis) - len(y2_axis)):
    #         y2_axis.append(0)
    #     logger.debug("y2_axis \n %s" % y2_axis)

    #     criterion = 0
    #     for i in range(len(y1_axis)):
    #         criterion += math.pow((y1_axis[i] - y2_axis[i]), 2)
    #     logger.debug("Criterion %f" % criterion)

    #     criterion_url = get_url_with_credentials(
    #         output_storage_settings,
    #         output_prefix + os.path.join(self.output_dir, node_output_dir, "PSD_output", "criterion.txt"),
    #         is_relative_path=False)
    #     storage.put_file(criterion_url, str(criterion))

    #     return criterion

    #def curate_dataset(self, run_settings, experiment_id, base_dir, all_settings):
    #    return 0

    def process_outputs(self, run_settings, base_dir, output_url, output_storage_settings, offset):
        return
