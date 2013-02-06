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

import sys
import os
import time
import logging
import logging.config
import json
import os
import sys
import re
import tempfile
from itertools import product
from random import randrange
from django.template import Context, Template


logger = logging.getLogger(__name__)


from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, \
    UI, SmartConnector

from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, \
    DataObject

from bdphpcprovider.smartconnectorscheduler import botocloudconnector

from bdphpcprovider.smartconnectorscheduler.hrmcimpl import PackageFailedError
#from hrmcimpl import prepare_multi_input
#from hrmcimpl import _normalize_dirpath
#from hrmcimpl import _status_of_nodeset
from bdphpcprovider.smartconnectorscheduler.sshconnector import \
    find_remote_files, run_command, put_file

from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_settings, \
    get_run_info, get_filesys, get_file

from bdphpcprovider.smartconnectorscheduler.sshconnector import get_package_pids, open_connection

class BadSpecificationError(Exception):
    pass

class Run(Stage):
    """
    Start applicaiton on nodes and return status
    """
    def __init__(self):
        self.numbfile = 0
        self.initial_numbfile = 1

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.
        # input_dir is assumed to be populated.
        '''
        TODO: - uncomment during transformation is in progress
              - change context to self.settings
              - move the code after self.settings.update

               self.iter_inputdir = "input"
        '''

        print "Run stage triggered"
        print __name__
        logger.debug("context = %s" % context)
        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        self.settings.update(run_info)
        logger.debug("settings = %s" % self.settings)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.iter_inputdir = "input_%s" % self.id
        else:
            self.iter_inputdir = "input"

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'setup_finished' in self.settings:
            setup_nodes = self.settings['setup_finished']
            logger.debug("setup_nodes = %s" % setup_nodes)
            packaged_nodes = len(botocloudconnector.get_rego_nodes(self.group_id, self.settings))
            logger.debug("packaged_nodes = %s" % packaged_nodes)

            if 'runs_left' in self.settings:
                logger.debug("found runs_left")
                return False

            if packaged_nodes == setup_nodes:
                return True
            else:
                logger.error("Indicated number of setup nodes does not match allocated number")
                logger.error("%s != %s" % (packaged_nodes, setup_nodes))
                return False
        else:
            logger.info("setup was not finished")
            return False

    def run_task(self, instance_id, settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.info("run_task %s" % instance_id)
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip,
                              settings=settings)
        pids = get_package_pids(ssh, settings['COMPILE_FILE'])
        logger.debug("pids=%s" % pids)
        if len(pids) > 1:
            logger.error("warning:multiple packages running")
            raise PackageFailedError("multiple packages running")
        run_command(ssh, "cd %s; ./%s >& %s &\
        " % (os.path.join(settings['PAYLOAD_DESTINATION'],
                          settings['PAYLOAD_CLOUD_DIRNAME']),
             settings['COMPILE_FILE'], "output"))

        import time
        attempts = settings['RETRY_ATTEMPTS']
        logger.debug("checking for package start")
        for x in range(0, attempts):
            time.sleep(5)  # to give process enough time to start
            pids = get_package_pids(ssh, settings['COMPILE_FILE'])
            logger.debug("pids=%s" % pids)
            if pids:
                break
        else:
            raise PackageFailedError("package did not start")
        # pids should have maximum of one element
        return pids

    def job_finished(instance_id, settings):
        """
            Return True if package job on instance_id has job_finished
        """
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip, settings=settings)
        pids = get_package_pids(ssh, settings['COMPILE_FILE'])
        logger.debug("pids=%s" % repr(pids))
        return pids == [""]

    def run_multi_task(self, group_id, iter_inputdir, settings):
        """
        Run the package on each of the nodes in the group and grab
        any output as needed
        """
        nodes = botocloudconnector.get_rego_nodes(group_id, settings)

        pids = []
        for node in nodes:
            try:
                instance_id = node.id
                pids_for_task = self.run_task(instance_id, settings)
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package on node %s" % node)
                #TODO: cleanup node of copied input files etc.
            else:
                pids.append(pids_for_task)

        all_pids = dict(zip(nodes, pids))
        return all_pids


    # def _create_input(self, instance_id, seeds, node, fsys):
    #     """
    #     Move the input files to the VM
    #     """
    #     ip = get_instance_ip(instance_id, self.settings)
    #     ssh = open_connection(ip_address=ip, settings=self.settings)

    #     # get all files from the payload directory
    #     dest_files = find_remote_files(ssh, os.path.join(self.settings['DEST_PATH_PREFIX'],
    #         self.settings['PAYLOAD_CLOUD_DIRNAME']))
    #     logger.debug("dest_files=%s" % dest_files)

    #     # keep results of setup stages
    #     for f in [self.settings['COMPILE_FILE'], "..", "."]:
    #         try:
    #             dest_files.remove(os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                 self.settings['PAYLOAD_CLOUD_DIRNAME'], f))
    #         except ValueError:
    #             logger.info("no %s found to remove" % f)

    #     logger.debug("dest_files=%s" % dest_files)
    #     # and delete all the rest
    #     for f in dest_files:
    #         run_command(ssh, "/bin/rm -f %s" % f)

    #     fsys.upload_input(ssh, self.iter_inputdir, os.path.join(
    #         self.settings['DEST_PATH_PREFIX'],
    #         self.settings['PAYLOAD_CLOUD_DIRNAME']))
    #     run_command(ssh, "cd %s; cp rmcen.inp rmcen.inp.orig" %
    #                 (os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                               self.settings['PAYLOAD_CLOUD_DIRNAME'])))
    #     run_command(ssh, "cd %s; dos2unix rmcen.inp" %
    #                 (os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                               self.settings['PAYLOAD_CLOUD_DIRNAME'])))
    #     run_command(ssh, "cd %s; sed -i '/^$/d' rmcen.inp" %
    #                 (os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                               self.settings['PAYLOAD_CLOUD_DIRNAME'])))
    #     run_command(ssh, "cd %s; sed -i 's/[0-9]*[ \t]*iseed.*$/%s\tiseed/' rmcen.inp" %
    #                 (os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                               self.settings['PAYLOAD_CLOUD_DIRNAME']), seeds[node]))
    #     run_command(ssh, "cd %s; sed -i 's/[0-9]*[ \t]*numbfile.*$/%s\tnumbfile/' rmcen.inp" %
    #                 (os.path.join(self.settings['DEST_PATH_PREFIX'],
    #                               self.settings['PAYLOAD_CLOUD_DIRNAME']), self.numbfile))
    #     self.numbfile += 1



    def _generate_variations(self, template, maps, initial_numbfile):

        # FIXME: doesn't handle multipe template files together
        res = []
        numbfile = initial_numbfile
        for iter, template_map in enumerate(maps):
            print "iter #%d" % iter
            temp_num = 0
            # ensure ordering of the template_map entries
            map_keys = template_map.keys()
            map_ranges = [list(template_map[x]) for x in map_keys]
            for z in product(*map_ranges):
                context = {}
                for i, k in enumerate(map_keys):
                    context[k] = str(z[i])  # str() so that 0 doesn't default value
                context['run_counter'] = numbfile
                numbfile += 1
                print context
                t = Template(template)
                con = Context(context)
                res.append((t.render(con), context))
                temp_num += 1
            print "%d files created" % (temp_num)

        return res

    def _prepare_input(self, context):
        """
        """
        fs = get_filesys(context)
        logger.debug("fs= %s GLobal %s" % (fs, fs.global_filesystem))

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        #get initial seed
        # FIXME: this is domain specific code
        if 'seed' in self.settings:
            seed = self.settings['seed']
        else:
            seed = 42
            logger.warn("No seed specified. Using default value")

        # come in with N input directoires

        tpattern = "(.*)_template"
        template_pat = re.compile(tpattern)
        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
        node_ind = 0
        logger.debug("Iteration Inpt dir %s" % self.iter_inputdir)
        input_dirs = fs.get_local_subdirectories(self.iter_inputdir)
        for input_dir in input_dirs:
            logger.debug("Inpt dir %s" % input_dir)

            if not fs.isdir(self.iter_inputdir, input_dir):
                continue

            # get any templated files
            variations = {}
            for fname in fs.get_local_subdirectory_files(self.iter_inputdir, input_dir):
                logger.debug("trying %s/%s/%s" % (self.iter_inputdir, input_dir, fname))
                data_object = fs.retrieve_under_dir(self.iter_inputdir, input_dir, fname)

                mat = template_pat.match(fname)
                if mat:
                    # template file
                    template = data_object.retrieve()
                    logger.debug("template content = %s" % template)
                    #
                    num_dim = 1


                    if num_dim == 1:
                        N = context['number_vm_instances']
                        map = {
                            'temp': [300],
                            'iseed': [randrange(0, self.settings['MAX_SEED_INT']) for x in xrange(0, N)],
                            'istart': [1 if self.id > 0  else 2]
                        }
                    elif num_dim == 2:
                        self.threshold = context['threshold']
                        N = self.threshold[0]
                        map = {
                            'temp': [300],
                            'iseed': [randrange(0, self.settings['MAX_SEED_INT']) for x in xrange(0, 4 * N)],
                            'istart': [2]

                        }

                        if self.id > 0:
                            map = {
                                'temp': [i for i in [300, 700, 1100, 1500]],
                                'iseed': [randrange(0, self.settings['MAX_SEED_INT'])],
                                'istart': [1]

                                }
                    else:
                        logger.error("Uknown dimensionality of problem")
                        raise  BadSpecificationError()

                    if not mat.groups():
                        logger.info("found odd template matching file %s" % fname)
                    else:

                        base_fname = mat.group(1)
                        logger.debug("base_fname=%s" % base_fname)
                        # generates a set of variations for the template fname
                        variation_set = self._generate_variations(template,
                            [map], self.initial_numbfile)
                        self.initial_numbfile += len(variation_set)
                        variations[base_fname] =variation_set
            else:
                # normal file
                pass

            logger.debug("variations = %s" % variations)
            # generate variations for the input_dir
            for var_fname in variations.keys():
                logger.debug("var_fname=%s" % var_fname)
                for var_content, values in variations[var_fname]:
                    logger.debug("var_content = %s" % var_content)
                    var_node = nodes[node_ind]
                    node_ind += 1
                    ip = botocloudconnector.get_instance_ip(var_node.id, self.settings)
                    ssh = open_connection(ip_address=ip, settings=self.settings)

                    # Cleanup any existing runs already there
                    # get all files from the payload directory
                    dest_files = find_remote_files(ssh,
                        os.path.join(self.settings['PAYLOAD_DESTINATION'],
                        self.settings['PAYLOAD_CLOUD_DIRNAME']))

                    # keep the compile exec from setup
                    for f in [self.settings['COMPILE_FILE'], "..", "."]:
                        try:
                            dest_files.remove(os.path.join(self.settings['PAYLOAD_DESTINATION'],
                                self.settings['PAYLOAD_CLOUD_DIRNAME'], f))
                        except ValueError:
                            logger.info("no %s found to remove" % f)

                    logger.debug("dest_files=%s" % dest_files)
                    # and delete all the rest
                    for f in dest_files:
                        logger.debug("deleting remote %s" % f)
                        run_command(ssh, "/bin/rm -f %s" % f)

                    # first copy up all existing input files to new variation
                    fs.upload_iter_input_dir(ssh, self.iter_inputdir, input_dir, os.path.join(
                        self.settings['PAYLOAD_DESTINATION'],
                        self.settings['PAYLOAD_CLOUD_DIRNAME']))

                    # FIXME: handle exceptions

                    # then create template variated file
                    varied_fdir = tempfile.mkdtemp()
                    print "varied_fdir=%s" % varied_fdir
                    fpath = os.path.join(varied_fdir, var_fname)
                    f = open(fpath, "w")
                    f.write(var_content)
                    f.close()

                    # plus store used val in substitution incase next iter needs them.
                    values_fname = "%s_values" % var_fname
                    vpath = os.path.join(varied_fdir, values_fname)
                    v = open(vpath, "w")
                    v.write(json.dumps(values))
                    v.close()

                    # and overwrite on the remote
                    put_file(ssh, varied_fdir, var_fname, os.path.join(
                        self.settings['PAYLOAD_DESTINATION'],
                        self.settings['PAYLOAD_CLOUD_DIRNAME']))
                    put_file(ssh, varied_fdir, values_fname, os.path.join(
                        self.settings['PAYLOAD_DESTINATION'],
                        self.settings['PAYLOAD_CLOUD_DIRNAME']))


                    # cleanup
                    #import shutil
                    #shutil.rmtree(varied_fdir)


        # # NOTE we assume that correct local file system has been created.

        # import random
        # random.seed(seed)

        # seeds = {}

        # for node in nodes:
        #     # FIXME: is the random supposed to be positive or negative?
        #     seeds[node] = random.randrange(0, self.settings['MAX_SEED_INT'])
        # if seed:
        #     print ("seed for full package run = %s" % seed)
        # else:
        #     print ("seeds for each node in group %s = %s"
        #            % (self.group_id, [(x.name, seeds[x])
        #                  for x in seeds.keys()]))

        # logger.debug("seeds = %s" % seeds)

        # Get starting value for numbfile from new input file
        # each deployed rmcen.inp has numbfile relative to this.
        # rmcen = fsys.retrieve_new(self.iter_inputdir, "rmcen.inp")
        # text = rmcen.retrieve()
        # p = re.compile("^([0-9]*)[ \t]*numbfile.*$", re.MULTILINE)
        # m = p.search(text)
        # if m:
        #     self.numbfile = int(m.group(1))
        # else:
        #     logger.error("could not find numbfile in rmcen.inp")
        #     self.numbfile = 100  # should not collide with other previous iterations.

        # # copy up the new input files to VMs
        # for node in nodes:
        #     instance_id = node.id
        #     logger.info("prepare_input %s %s" % (instance_id, self.iter_inputdir))
        #     self._create_input(instance_id, seeds, node, fsys)



    def process(self, context):

        logger.debug("processing run stage")
        logger.debug("preparing inputs")

        self._prepare_input(context)
        logger.debug("running tasks")

        try:
            pids = self.run_multi_task(self.group_id, self.iter_inputdir, self.settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages")
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)
        return pids

    def output(self, context):
        """
        Assume that no nodes have finished yet and indicate to future stages
        """
        #TODO: make function for get fsys, run_info and settings
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        run_info_file = get_file(fsys, "default/runinfo.sys")
        logger.debug("run_info_file= %s" % run_info_file)

        settings_text = run_info_file.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)



        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
        logger.debug("nodes = %s" % nodes)

        config = json.loads(settings_text)
        # We assume that none of runs have finished yet.
        config['runs_left'] = len(nodes)  # FIXME: possible race condition?
        #config['error_nodes'] = len(error_nodes)
        logger.debug("config=%s" % config)
        run_info_text = json.dumps(config)
        run_info_file.setContent(run_info_text)
        logger.debug("run_info_file=%s" % run_info_file)
        fsys.update("default", run_info_file)
        # FIXME: check to make sure not retriggered

        return context