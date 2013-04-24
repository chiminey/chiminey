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

import re
import os
import logging
import fnmatch

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages


logger = logging.getLogger(__name__)


class Transform(Stage):
    """
        Convert output into input for next iteration.
    """
    # FIXME: put part of config file, or pull from original input file
    domain_input_files = ['pore.xyz', 'sqexp.dat', 'grexp.dat', ]

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.boto_settings = user_settings.copy()
        logger.debug("creating transform")
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        pass

    def triggered(self, run_settings):

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/create', u'group_id'):
            self.group_id = run_settings['http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
        logger.debug("group_id = %s" % self.group_id)

        # self.group_id = self.settings['group_id']

        import ast
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'threshold'):
            # FIXME: need to validate this output to make sure list of int
            self.threshold = ast.literal_eval(run_settings['http://rmit.edu.au/schemas/hrmc'][u'threshold'])
        else:
            logger.warn("no threshold found when expected")
            return False
        logger.debug("threshold = %s" % self.threshold)

        # self.threshold = context['threshold']

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.output_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "output_%s" % self.id)
            self.input_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "input_%d" % self.id)
            self.new_input_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "input_%d" % (self.id + 1))
        else:
            # FIXME: Not clear that this a valid path through stages
            self.output_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "output")
            self.output_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "input")
            self.new_input_dir = os.path.join("%s%s" % (self.job_dir, self.contextid), "input_1")

        # if 'id' in self.settings:
        #     self.id = self.settings['id']
        #     self.output_dir = "output_%d" % self.id
        #     self.input_dir = "input_%d" % self.id
        #     self.new_input_dir = "input_%d" % (self.id + 1)
        # else:
        #     # FIXME: Not clear that this a valid path through stages
        #     self.output_dir = "output"
        #     self.output_dir = "input"
        #     self.new_input_dir = "input_1"

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/converge', u'converged'):
            # FIXME: should use NUMERIC for bools, so use 0,1 and natural comparison will work.
            self.converged = (run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'] == u'True')
        else:
            self.converged = False

        # if 'converged' in self.settings:
        #     self.converged = self.settings['converged']
        # else:
        #     self.converged = False

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
            self.runs_left = run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left']
            if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform', u'transformed'):
                self.transformed = (run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'] == u'True')
            else:
                self.transformed = False
            if (self.runs_left == 0) and (not self.transformed) and (not self.converged):
                return True
            else:
                logger.debug("%s %s %s" % (self.runs_left, self.transformed, self.converged))
                pass

        # if 'runs_left' in self.settings:
        #     self.runs_left = self.settings["runs_left"]
        #     if 'transformed' in self.settings:
        #         self.transformed = self.settings['transformed']
        #     else:
        #         self.transformed = False
        #     if self.runs_left == 0 and not self.transformed and not self.converged:
        #         logger.debug("Transform triggered")
        #         return True

        return False

    def copy_files_with_pattern(self, fsys, source_path,
                             dest_path, pattern):
        """
        """
        _, fnames = fsys.listdir(source_path)
        for f in fnames:
            if fnmatch.fnmatch(f, pattern):
                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(source_path, f), is_relative_path=True)
                dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(dest_path, f), is_relative_path=True)
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

        # import time
        # start_time = time.time()
        # logger.debug("Start time %f "% start_time)

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/group_id_dir')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/max_seed_int')
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
        self.boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
        key_file = hrmcstages.retrieve_private_key(self.boto_settings, self.user_settings['nectar_private_key'])
        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file


        output_url = smartconnector.get_url_with_pkey(self.boto_settings,
            self.output_dir, is_relative_path=True)
        # Should this be output_dir or root of remotesys?
        fsys = hrmcstages.get_filesystem(output_url)
        node_output_dirs, _ = fsys.listdir(self.output_dir)
        logger.debug("node_output_dirs=%s" % node_output_dirs)
        self.audit = ""
        result_info = []
        for node_output_dir in node_output_dirs:

            rmcen_url = smartconnector.get_url_with_pkey(self.boto_settings,
                os.path.join(self.output_dir, node_output_dir, 'rmcen.inp'), is_relative_path=True)

            logger.debug("rmcen_url=%s" % rmcen_url)
            rmcen_content = hrmcstages.get_file(rmcen_url)
            logger.debug("rmcen_content=%s" % rmcen_content)
            # Get numbfile from rmcen.inp
            numb = [x.split()[0] for x in rmcen_content.split('\n') if 'numbfile' in x]
            if numb:
                number = int(numb[0])
            else:
                raise ValueError("No numbfile record found")

            logger.debug("number=%s" % number)
            criterion = self.compute_psd_criterion(node_output_dir, fsys)
            logger.debug("criterion=%s" % criterion)
            #criterion = self.compute_hrmc_criterion(number, node_output_dir, fs)
            index = 0
            result_info.append((node_output_dir, index, number, criterion))

        # Get Maximum numbfile in all previous runs
        max_numbfile = max([x[2] for x in result_info])
        logger.debug("maximum numbfile value=%s" % max_numbfile)

        # Get informatiion about minimum criterion previous run.
        logger.debug("result_info=%s" % result_info)
        result_info.sort(key=lambda x: int(x[3]))
        logger.debug("result_info=%s" % result_info)

        total_picks = 1
        if len(self.threshold) > 1:
            for i in self.threshold:
                total_picks *= self.threshold[i]
        else:
            total_picks = self.threshold[0]

        if result_info:
            for i in range(0, total_picks):
                (best_node_dir, best_index, number, criterion) = result_info[i]
                self.new_input_node_dir = os.path.join(self.new_input_dir, best_node_dir)
                logger.debug("New input node dir %s" % self.new_input_node_dir)

                # Transfer rmcen.inp to next iteration inputdir initially unchanged
                source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.output_dir, best_node_dir, 'rmcen.inp'), is_relative_path=True)
                dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.new_input_node_dir, 'rmcen.inp'), is_relative_path=True)
                rmcen_content = hrmcstages.get_file(source_url)
                hrmcstages.put_file(dest_url, rmcen_content)

                # Move all existing domain input files unchanged to next input directory
                for f in self.domain_input_files:
                    source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir, best_node_dir, f), is_relative_path=True)
                    dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.new_input_node_dir, f), is_relative_path=True)
                    content = hrmcstages.get_file(source_url)
                    hrmcstages.put_file(dest_url, content)

                pattern = "*_values"
                self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, best_node_dir),
                    self.new_input_node_dir, pattern)

                pattern = "*_template"
                self.copy_files_with_pattern(fsys, os.path.join(self.output_dir, best_node_dir),
                    self.new_input_node_dir, pattern)

                # NB: Converge stage triggers based on criterion value from audit.

                info = "Run %s preserved (error %s)\n" % (number, criterion)
                audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.new_input_node_dir, 'audit.txt'), is_relative_path=True)
                hrmcstages.put_file(audit_url, info)
                logger.debug("audit=%s" % info)
                self.audit += info

                logger.debug("best_node_dir=%s" % best_node_dir)
                logger.debug("best_index=%s" % best_index)
                logger.debug("number=%s" % number)

                try:
                    xyzfiles = ['hrmc%s.xyz' % str(number).zfill(2)]
                    xyzfile_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            best_node_dir, 'hrmc%s.xyz' % str(number).zfill(2)), is_relative_path=True)
                    f = hrmcstages.get_file(xyzfile_url)  # FIXME: check that get_file can raise IOError
                except IOError:
                    logger.warn("no hrmcstages found")
                logger.debug("xyzfiles=%s " % xyzfiles)

                found = False
                for file_name in xyzfiles:
                    # TODO: len(xyzfiles) == 1
                    if file_name == 'hrmc%s.xyz' % (str(number).zfill(2)):
                        logger.debug("%s -> %s" % (file_name, 'initial.xyz'))
                        try:

                            source_url = smartconnector.get_url_with_pkey(self.boto_settings,
                                os.path.join(self.output_dir, best_node_dir, file_name), is_relative_path=True)
                            dest_url = smartconnector.get_url_with_pkey(self.boto_settings,
                                os.path.join(self.new_input_node_dir, 'initial.xyz'), is_relative_path=True)
                            content = hrmcstages.get_file(source_url)
                            hrmcstages.put_file(dest_url, content)
                            # self.copy_file(fsys,
                            #     os.path.join(self.output_dir, best_node_dir, file_name),
                            #     os.path.join(self.new_input_node_dir, 'initial.xyz'))
                            # fs.copy(self.output_dir, best_node_dir,
                            #     file_name, self.new_input_dir,
                            #     'initial.xyz', overwrite=True)
                        except IOError as e:
                            logger.warn("no %s found in  %s/%s: %s"
                                        % (file_name, self.output_dir, best_node_dir, e))
                            continue
                        else:
                            found = True
                if not found:
                    logger.warn("No matching %s file found to transfer")

                new_rmcen_url = smartconnector.get_url_with_pkey(self.boto_settings,
                    os.path.join(self.new_input_node_dir, 'rmcen.inp'), is_relative_path=True)
                new_rmcen_content = hrmcstages.get_file(new_rmcen_url)

                # Change numfile to be higher than any of previous iteration
                p = re.compile("^([0-9]*)[ \t]*numbfile.*$", re.MULTILINE)
                m = p.search(new_rmcen_content)
                if m:
                    numbfile = int(m.group(1))
                else:
                    logger.warn("could not find numbfile in rmcen.inp")
                    numbfile = self.id
                new_rmcen_content = re.sub(p, "%d    numbfile" % (max_numbfile + 1), new_rmcen_content)
                logger.debug("numfile = %d" % numbfile)

                # Change istart from 2 to 1 after first iteration
                p = re.compile("^([0-9]*)[ \t]*istart.*$", re.MULTILINE)
                m = p.search(new_rmcen_content)
                if m:
                    logger.debug("match = %s" % m.groups())
                    new_rmcen_content = re.sub(p, "1     istart", new_rmcen_content)
                else:
                    logger.warn("Cloud not find istart in rmcen.inp")
                logger.debug("new_rmcen_content = %s" % new_rmcen_content)

                # FIXME: assume we always overwrite to local storage
                hrmcstages.put_file(new_rmcen_url, new_rmcen_content)

                self.audit += "spawning diamond runs\n"

        else:
            # FIXME: can we carry on here?
            logger.warning("no output directory found")
            (best_node_dir, best_index, number, criterion) = ("", 0, 0, 0)  # ?

    def output(self, run_settings):
        logger.debug("transform.output")
        audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.new_input_dir, 'audit.txt'), is_relative_path=True)
        hrmcstages.put_file(audit_url, self.audit)

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/transform'):
            run_settings['http://rmit.edu.au/schemas/stages/transform'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/transform'][u'transformed'] = True

        print "End of Transformation: \n %s" % self.audit

        return run_settings

    def compute_hrmc_criterion(self, number, node_output_dir, fs):
        grerr_file = 'grerr%s.dat' % str(number).zfill(2)
        logger.debug("grerr_file=%s " % grerr_file)
        grerr_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, 'grerr%s.dat' % str(number).zfill(2)), is_relative_path=True)
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

        psd_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "psd.dat"), is_relative_path=True)
        psd = hrmcstages.get_filep(psd_url)

        # psd_exp = os.path.join(globalFileSystem,
        #                        self.output_dir, node_output_dir,
        #                        "PSD_output/PSD_exp.dat")
        psd_url = smartconnector.get_url_with_pkey(self.boto_settings,
                        os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "PSD_exp.dat"), is_relative_path=True)
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
            os.path.join(self.output_dir, node_output_dir, "PSD_output", "criterion.txt"), is_relative_path=True)
        hrmcstages.put_file(criterion_url, str(criterion))

        # criterion_file = DataObject('criterion.txt')
        # criterion_file.create(str(criterion))
        # criterion_path = os.path.join(self.output_dir,
        #                               node_output_dir, "PSD_output")
        # fs.create(criterion_path, criterion_file)

        return criterion
