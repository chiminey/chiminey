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
import logging
import logging.config

from hrmcstages import get_settings
from hrmcstages import get_run_info
from hrmcstages import get_filesys
from hrmcstages import update_key
from filesystem import DataObject

from smartconnector import Stage

logger = logging.getLogger('stages')


class Transform(Stage):
    """
        Convert output into input for next iteration.
    """
    # FIXME: put part of config file, or pull from original input file
    input_files = ['pore.xyz', 'sqexp.dat', 'grexp.dat']

    def __init__(self):
        logger.debug("creating transform")
        # alt_specfication implements revised set of specifications from product
        # owners. Old way is deprecated, to be removed in due time.
        self.alt_specification = True

        pass

    def triggered(self, context):
        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)
        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)
        self.group_id = run_info['group_id']
        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)
        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.output_dir = "output_%d" % self.id
            self.input_dir = "input_%d" % self.id
            self.new_input_dir = "input_%d" % (self.id + 1)
        else:
            self.output_dir = "output"
            self.output_dir = "input"
            self.new_input_dir = "input_1"

        if 'converged' in self.settings:
            self.converged = self.settings['converged']
        else:
            self.converged = False

        if 'runs_left' in self.settings:
            self.runs_left = self.settings["runs_left"]
            if 'transformed' in self.settings:
                self.transformed = self.settings['transformed']
            else:
                self.transformed = False
            if self.runs_left == 0 and not self.transformed and not self.converged:
                return True
        return False

    def process(self, context):

        self.audit = ""
        res = []
        fs = get_filesys(context)

        # Analyse each run in the previous iteration diamond
        node_output_dirs = fs.get_local_subdirectories(self.output_dir)
        logger.debug("node_output_dirs=%s" % node_output_dirs)
        for node_output_dir in node_output_dirs:
            if not fs.isdir(self.output_dir, node_output_dir):
                logger.warn("%s is not a directory" % node_output_dir)
                # FIXME: do we really want to skip here?
                continue
            #file_rmcen = os.path.join(node_output_dir, 'rmcen.inp')
            if not fs.exists(self.output_dir, node_output_dir, 'rmcen.inp'):
                logger.warn("rmcen.inp not found")
                # FIXME: do we really want to skip here?
                continue
            if not fs.isfile(self.output_dir, node_output_dir, 'rmcen.inp'):
                logger.warn("rmcen.inp not a file")
                # FIXME: do we really want to skip here?
                continue

            # Get numbfile from rmcen.inp
            numb = [x.split()[0] for x
                in fs.retrieve_under_dir(self.output_dir,
                                         node_output_dir,
                                         'rmcen.inp').retrieve().split('\n')
                if 'numbfile' in x]
            if numb:
                number = int(numb[0])
            else:
                raise ValueError("No numbfile record found")

            if self.alt_specification:
                try:
                    grerr_files = ['grerr%s.dat' % str(number).zfill(2)]
                    f = fs.retrieve_under_dir(self.output_dir,
                                          node_output_dir,
                                         'grerr%s.dat' % str(number).zfill(2)).retrieve()
                except IOError:
                        logger.warn("no grerr found")
            else:
                # for each grerr*.dat file, get criterion
                grerr_files = fs.glob(self.output_dir, node_output_dir, 'grerr[0-9]+.dat')
                grerr_files.sort()

            logger.debug("grerr_files=%s " % grerr_files)
            criterions = []
            for (index, f) in enumerate(grerr_files):

                grerr_content = fs.retrieve_under_dir(self.output_dir,
                                                  node_output_dir,
                                                  grerr_files[-1]).retrieve()
                logger.debug("grerr_content=%s" % grerr_content)
                try:
                    criterion = float(grerr_content.strip().split('\n')[-1]
                        .split()[1])
                except ValueError as e:
                    logger.warn("invalid criteron found in grerr "
                        + "file for  %s/%s: %s"
                        % (self.output_dir, node_output_dir, e))
                    continue
                logger.debug("criterion=%s" % criterion)
                criterions.append((index, f, criterion))

            # Find minimum criterion
            criterions.sort(key=lambda x: x[2])
            if criterions:
                grerr_info = criterions[0]
            else:
                logger.error("no grerr files found")
                grerr_info = ()  # FIXME: can recover from this?
            criterion = grerr_info[2]
            f = grerr_info[1]

            res.append((node_output_dir, index, number, criterion, f))

        # Get Maximum numbfile in all previous runs
        max_numbfile = max([x[2] for x in res])
        logger.debug("maximum numbfile value=%s" % max_numbfile)

        # Get informatiion about minimum criterion previous run.
        logger.debug("res=%s" % res)
        res.sort(key=lambda x: int(x[3]))
        logger.debug("res=%s" % res)
        if res:
            (best_node_dir, best_index, number, criterion, grerr_file) = res[0]
        else:
            # FIXME: can we carry on here?
            logger.warning("no output directory found")
            (best_node_dir, best_index, number, criterion, grerr_file) = ("", 0, 0, 0, "")  # ?

        # NB: Converge stage triggers based on criterion value from audit.
        self.audit += "Run %s preserved (error %s)\n" % (number, criterion)
        logger.debug("best_node_dir=%s" % best_node_dir)
        logger.debug("best_index=%s" % best_index)
        logger.debug("grerr_file=%s" % grerr_file)
        logger.debug("number=%s" % number)

        fs.create_local_filesystem(self.new_input_dir)

        # Transfer rmcen.inp to next iteration inputdir initially unchanged
        fs.copy(self.output_dir, best_node_dir,
                'rmcen.inp', self.new_input_dir, 'rmcen.inp')

        # Move all existing input files unchanged to next input directory
        for f in self.input_files:
            try:
                fs.copy(self.output_dir, best_node_dir,
                        f, self.new_input_dir, f)
            except IOError as e:
                logger.warn("no %s found in  %s/%s: %s"
                    % (f, self.output_dir, best_node_dir, e))
                continue

        if self.alt_specification:
            try:
                xyzfiles = ['hrmc%s.xyz' % str(number).zfill(2)]
                f = fs.retrieve_under_dir(self.output_dir,
                             best_node_dir,
                            'hrmc%s.xyz' % str(number).zfill(2)).retrieve()
            except IOError:
                logger.warn("no hrmcstages found")
        else:
            # Copy hrmc[best_index].xyz file from best run new input directory
            # as initial.xyz
            xyzfiles = fs.glob(self.output_dir, best_node_dir, 'hrmc[0-9]+\.xyz')
            logger.debug("xyzfiles=%s " % xyzfiles)
            xyzfiles.sort()  # FIXME: assume we use only the last
        logger.debug("xyzfiles=%s " % xyzfiles)
        found = False
        for file_name in xyzfiles:
            if file_name == 'hrmc%s.xyz' % (str(number).zfill(2)):
            #if file_name == grerr_file:
                logger.debug("%s -> %s" % (file_name, 'initial.xyz'))
                try:
                    fs.copy(self.output_dir, best_node_dir,
                            file_name, self.new_input_dir,
                            'initial.xyz', overwrite=True)
                except IOError as e:
                    logger.warn("no %s found in  %s/%s: %s"
                        % (file_name, self.output_dir, best_node_dir, e))
                    continue
                found = True
        if not found:
            logger.warn("No matching %s file found to transfer" % grerr_file)
        rmcen = fs.retrieve_new(self.new_input_dir, "rmcen.inp")
        text = rmcen.retrieve()

        # Change numfile to be higher than any of previous iteration
        p = re.compile("^([0-9]*)[ \t]*numbfile.*$", re.MULTILINE)
        m = p.search(text)
        if m:
            numbfile = int(m.group(1))
        else:
            logger.warn("could not find numbfile in rmcen.inp")
            numbfile = self.id
        text = re.sub(p, "%d    numbfile" % (max_numbfile + 1), text)
        logger.debug("numfile = %d" % numbfile)

        # Change istart from 2 to 1 after first iteration
        p = re.compile("^([0-9]*)[ \t]*istart.*$", re.MULTILINE)
        m = p.search(text)
        if m:
            logger.debug("match = %s" % m.groups())
            text = re.sub(p, "1     istart", text)
        else:
            logger.warn("Cloud not find istart in rmcen.inp")
        logger.debug("text = %s" % text)

        # Write back changes
        rmcen.setContent(text)
        logger.debug("rmcen=%s" % rmcen)
        fs.update(self.new_input_dir, rmcen)

        self.audit += "spawning diamond runs\n"

    def output(self, context):
        logger.debug("transform.output")

        audit = DataObject('audit.txt')
        audit.create(self.audit)
        logger.debug("audit=%s" % audit)
        fs = get_filesys(context)
        fs.create(self.new_input_dir, audit)

        update_key('transformed', True, context)

        return context
