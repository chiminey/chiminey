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

from hrmcstages import get_settings
from hrmcstages import get_run_info
from hrmcstages import get_filesys
#from filesystem import FileSystem
#from filesystem import DataObject
from hrmcstages import update_key

from smartconnector import Stage

import logging
import logging.config

logger = logging.getLogger('stages')


class Transform(Stage):
    """
        Convert output into input for next iteration.
    """

    def __init__(self):
        logger.debug("creating transform")
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
        import re

        self.audit = ""
        res = []
        fs = get_filesys(context)

        # for each run in the diamon
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
            # get numbfile
            numb = [x.split()[0] for x
                in fs.retrieve_under_dir(self.output_dir,
                                         node_output_dir,
                                         'rmcen.inp').retrieve().split('\n')
                if 'numbfile' in x]
            if numb:
                number = int(numb[0])
            else:
                raise ValueError("No numbfile record found")

            grerr_files = fs.get_local_subdirectory_files(
                self.output_dir,
                node_output_dir)
            logger.debug("grerr_files=%s " % grerr_files)
            pat = re.compile('grerr[0-9]+.dat')
            grerr_files = [x for x in grerr_files if pat.match(x)]
            grerr_files.sort()  # FIXME: only guaranteed to sort grerr 01-09
            logger.debug("grerr_files=%s " % grerr_files)
            grerr_content = fs.retrieve_under_dir(self.output_dir,
                                                  node_output_dir,
                                                  grerr_files[-1]).retrieve()
            logger.debug("grerr_content=%s" % grerr_content)
            try:
                criterion = int(grerr_content.strip().split('\n')[-1]
                    .split()[0])
            except ValueError as e:
                logger.warn("invalid criteron found in grerr "
                    + "file for  %s/%s: %s"
                    % (self.output_dir, node_output_dir, e))
                continue
            logger.debug("criterion=%s" % criterion)
            res.append((node_output_dir, number, criterion))

        logger.debug("res=%s" % res)
        res = sorted(res, key=lambda x: x[2])
        logger.debug("res=%s" % res)
        if res:
            (best_node_dir, number, criterion) = res[0]
        else:
            # FIXME: can we carry on here?
            logger.warning("no output directory found")
            (best_node_dir, number, criterion) = (self.output_dir, 0, 0)  # ?

        self.audit += "Run %s preserved (error %s)\n" % (number, criterion)
        logger.debug("best_node_dir=%s" % best_node_dir)

        # FIXME: what is the number?  Is it just the iteration number of
        # something more?

        fs.create_local_filesystem(self.new_input_dir)

        # transfer rmcen.inp to next iteration inputdir
        fs.copy(self.output_dir, best_node_dir,
                'rmcen.inp', self.new_input_dir, 'rmcen.inp')

        for f in ['pore.xyz', 'sqexp.dat']:
            try:
                fs.copy(self.output_dir, best_node_dir,
                        f, self.new_input_dir, f)
            except IOError as e:
                logger.warn("no %s found in  %s/%s: %s"
                    % (f, self.output_dir, best_node_dir, e))
                continue

        # copy best hrmc*.xyz file to new input directory as initial.xyz
        # FIXME: what if there are multiple matches? DO we choose the largest?
        # TODO: make into globbing function in fsys
        xyzfiles = fs.get_local_subdirectory_files(self.output_dir,
                                                    best_node_dir)
        logger.debug("xyzfiles=%s " % xyzfiles)
        pat = re.compile('hrmc[0-9]+\.xyz')
        xyzfiles = [x for x in xyzfiles if pat.match(x)]
        logger.debug("xyzfiles=%s " % xyzfiles)

        xyzfiles.sort()  # FIXME: assume we use only the last
        logger.debug("xyzfiles=%s " % xyzfiles)

        for file_name in xyzfiles:
            try:
                fs.copy(self.output_dir, best_node_dir,
                        file_name, self.new_input_dir,
                        'initial.xyz', overwrite=True)
            except IOError as e:
                logger.warn("no %s found in  %s/%s: %s"
                    % (file_name, self.output_dir, best_node_dir, e))
                continue

        #NB: only works for small files
        rmcen = fs.retrieve_new(self.new_input_dir, "rmcen.inp")
        text = rmcen.retrieve()
        #logger.debug("text = %s" % text)

        # increment rmcen.input numbfile value.  FIXME: is this correct?
        p = re.compile("^([0-9]*)[ \t]*numbfile.*$", re.MULTILINE)

        # numbfile should match iteration number but read version first
        m = p.search(text)
        if m:
            numbfile = int(m.group(1))
        else:
            logger.warn("could not find numbfile in rmcen.inp")
            numbfile = self.id
        text = re.sub(p, "%d    numbfile" % (numbfile + 1), text)
        #logger.debug("text = %s" % text)

        logger.debug("numfile = %d" % numbfile)

        # change istart
        p = re.compile("^([0-9]*)[ \t]*istart.*$", re.MULTILINE)
        m = p.search(text)
        if m:
            logger.debug("match = %s" % m.groups())
            text = re.sub(p, "1     istart", text)
        else:
            logger.warn("Cloud not find istart in rmcen.inp")
        logger.debug("text = %s" % text)

        rmcen.setContent(text)
        logger.debug("rmcen=%s" % rmcen)
        fs.update(self.new_input_dir, rmcen)

        self.audit += "spawning diamond runs\n"

        '''
            def _kill_run(context):
        """ Based on information from the current run, decide whether
            to kill the current runs
        """
        #TODO:
        pass
        '''
    def output(self, context):

        update_key('transformed', True, context)

        return context
