# Copyright (C) 2016, RMIT University

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


from chiminey.storage import get_url_with_credentials
from chiminey.runsettings import getval, SettingNotFoundException

from chiminey import storage
from chiminey import mytardis
from chiminey.corestages import Transform


from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class HRMCTransform(Transform):

    SCHEMA_PREFIX = django_settings.SCHEMA_PREFIX
    VALUES_FNAME = "values"
    DOMAIN_INPUT_FILES = ['input_bo.dat', 'input_gr.dat', 'input_sq.dat']

    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem
        """
        logger.debug("settings_to_test=%s" % settings_to_test)
        error = []
        try:
            ast.literal_eval(getval(
                                         settings_to_test,
                                        '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX))
        except (ValueError, SettingNotFoundException):
            error.append("Cannot load threshold")

        if error:
            return (False, '. '.join(error))
        return (True, "ok")

    def is_triggered(self, run_settings):
        super_trigger = super(HRMCTransform, self).is_triggered(run_settings)

        if super_trigger:
            try:
                # FIXME: need to validate this output to make sure list of int
                ast.literal_eval(getval(
                                             run_settings,
                                            '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX))
            except (SettingNotFoundException, ValueError):
                logger.warn("no threshold found when expected")
                return False
        return super_trigger

    def process_outputs(self, run_settings, base_dir, output_url, all_settings, offset):

        # output_dir = 118.138.241.232/outptuersdfsd/sweep277/hrmc278/output_1
        # output_prefix = ssh://unix@
        # node_output_dir = 2

        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])

        id = int(getval(run_settings, '%s/system/id' % self.SCHEMA_PREFIX))
        iter_output_dir = os.path.join(os.path.join(base_dir, "output_%s" % id))
        logger.debug('iter_output_dir=%s' % iter_output_dir)
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        logger.debug('output_prefix=%s' % output_prefix)
        #iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)
        logger.debug('output_url=%s' % output_url)
        (scheme, host, iter_output_path, location, query_settings) = storage.parse_bdpurl(output_url)
        logger.debug("iter_output_path=%s" % iter_output_path)
        iter_out_fsys = storage.get_filesystem(output_url)
        logger.debug("iter_out_fsys=%s" % iter_out_fsys)
        node_output_dirnames, _ = iter_out_fsys.listdir(iter_output_path)
        logger.debug('node_output_dirnames=%s' % node_output_dirnames)
        self.audit = ""

        Node_info = namedtuple('Node_info',
            ['dirname', 'number', 'criterion'])

        # generate criterias
        self.outputs = []
        for node_output_dirname in node_output_dirnames:
            node_path = output_prefix + os.path.join(iter_output_dir, node_output_dirname)
            criterion = self.compute_psd_criterion(all_settings, node_path)
            #criterion = self.compute_hrmc_criterion(values_map['run_counter'], node_output_dirname, fs,)
            logger.debug("criterion abc=%s" % criterion)

            try:
                values_url = get_url_with_credentials(
                    all_settings, os.path.join(node_path,
                       self.VALUES_FNAME), is_relative_path=False)
                logger.debug("values_url=%s" % values_url)
                values_content = storage.get_file(values_url)

                logger.debug("values_file=%s" % values_url)
            except IOError:
                logger.warn("no values file found")
                values_map = {}
            else:
                values_map = dict(json.loads(values_content))
                self.outputs.append(Node_info(dirname=node_output_dirname,
                               number=values_map['run_counter'], criterion=criterion))

        if not self.outputs:
            logger.error("no ouput found for this iteration")
            return

        self.outputs.sort(key=lambda x: int(x.criterion))
        logger.debug("self.outputs=%s" % self.outputs)

        try:
            # FIXME: need to validate this output to make sure list of int
            threshold = ast.literal_eval(getval(run_settings, '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            logger.warn("no threshold found when expected")
            return False
        logger.debug("threshold = %s" % threshold)
        total_picks = 1
        if len(threshold) > 1:
            for i in threshold:
                total_picks *= threshold[i]
        else:
            total_picks = threshold[0]

        def copy_files_with_pattern(iter_out_fsys, source_path,
                                 dest_path, pattern, all_settings):
            """
            """
            output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])

            logger.debug('source_path=%s, dest_path=%s' % (source_path, dest_path))
            # (scheme, host, iter_output_path, location, query_settings) = storage.parse_bdpurl(source_path)
            _, node_output_fnames = iter_out_fsys.listdir(source_path)
            ip_address = all_settings['ip_address']
            for f in node_output_fnames:
                if fnmatch.fnmatch(f, pattern):
                    source_url = get_url_with_credentials(all_settings, output_prefix + os.path.join(ip_address, source_path, f), is_relative_path=False)
                    dest_url = get_url_with_credentials(all_settings, output_prefix + os.path.join(ip_address, dest_path, f), is_relative_path=False)
                    logger.debug('source_url=%s, dest_url=%s' % (source_url, dest_url))
                    content = storage.get_file(source_url)
                    storage.put_file(dest_url, content)

        # Make new input dirs
        new_input_dir = os.path.join(os.path.join(base_dir, "input_%d" % (id + 1)))
        for index in range(0, total_picks):
            Node_info = self.outputs[index]
            logger.debug("node_info.dirname=%s" % Node_info.dirname)
            logger.debug("Node_info=%s" % str(Node_info))

            new_input_path = os.path.join(new_input_dir,
                Node_info.dirname)
            logger.debug("New input node dir %s" % new_input_path)

            old_output_path = os.path.join(iter_output_dir, Node_info.dirname)

            # Move all existing domain input files unchanged to next input directory
            for f in self.DOMAIN_INPUT_FILES:
                source_url = get_url_with_credentials(
                    all_settings, output_prefix + os.path.join(old_output_path, f), is_relative_path=False)
                dest_url = get_url_with_credentials(
                    all_settings, output_prefix + os.path.join(new_input_path, f),
                    is_relative_path=False)
                logger.debug('source_url=%s, dest_url=%s' % (source_url, dest_url))

                content = storage.get_file(source_url)
                logger.debug('content collected')
                storage.put_file(dest_url, content)
                logger.debug('put successfully')

            logger.debug('put file successfully')
            pattern = "values"
            output_offset = os.path.join(os.path.join(offset, "output_%s" % id, Node_info.dirname))
            input_offset = os.path.join(os.path.join(offset, "input_%s" % (id + 1), Node_info.dirname))
            copy_files_with_pattern(iter_out_fsys,
                output_offset,
                input_offset, pattern,
                all_settings)

            pattern = "*_template"
            copy_files_with_pattern(iter_out_fsys,
                output_offset,
                input_offset, pattern,
                all_settings)

            # NB: Converge stage triggers based on criterion value from audit.
            logger.debug('starting audit')
            info = "Run %s preserved (error %s)\n" % (Node_info.number, Node_info.criterion)
            audit_url = get_url_with_credentials(
                all_settings, output_prefix +
                os.path.join(new_input_path, 'audit.txt'), is_relative_path=False)
            storage.put_file(audit_url, info)
            logger.debug("audit=%s" % info)
            logger.debug('1:audit_url=%s' % audit_url)
            self.audit += info

            # move xyz_final.xyz to initial.xyz
            source_url = get_url_with_credentials(
                all_settings, output_prefix + os.path.join(old_output_path, "xyz_final.xyz"), is_relative_path=False)
            logger.debug('source_url=%s' % source_url)
            dest_url = get_url_with_credentials(
                all_settings, output_prefix + os.path.join(new_input_path, 'input_initial.xyz'), is_relative_path=False)
            logger.debug('dest_url=%s' % dest_url)
            content = storage.get_file(source_url)
            logger.debug('content=%s' % content)
            storage.put_file(dest_url, content)
            self.audit += "spawning diamond runs\n"

        logger.debug("input_dir=%s" % (output_prefix + os.path.join(new_input_dir, 'audit.txt')))
        audit_url = get_url_with_credentials(
            all_settings, output_prefix + os.path.join(new_input_dir, 'audit.txt'), is_relative_path=False)
        logger.debug('audit_url=%s' % audit_url)
        storage.put_file(audit_url, self.audit)
        return self.outputs

    def compute_psd_criterion(self, all_settings, node_path):
        import math
        import os
        #globalFileSystem = fs.get_global_filesystem()
        # psd = os.path.join(globalFileSystem,
        #                    self.output_dir, node_output_dir,
        #                    "PSD_output/psd.dat")
        #Fixme replace all reference to files by parameters, e.g PSDCode
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        logger.debug('output_prefix=%s' % output_prefix)
        logger.debug('node_path=%s' % node_path)

        psd_url = get_url_with_credentials(all_settings,
                        os.path.join(node_path, "psd.dat"), is_relative_path=False)
        logger.debug('psd_url=%s' % psd_url)

        psd = storage.get_filep(psd_url)
        logger.debug('psd=%s' % psd._name)

        # psd_exp = os.path.join(globalFileSystem,
        #                        self.output_dir, node_output_dir,
        #                        "PSD_output/PSD_exp.dat")
        psd_url = get_url_with_credentials(
            all_settings,
                         os.path.join(node_path, "PSD_exp.dat"), is_relative_path=False)
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

        criterion_url = get_url_with_credentials(
            all_settings,
            os.path.join(node_path, "criterion.txt"),
            is_relative_path=False)
        storage.put_file(criterion_url, str(criterion))

        return criterion
