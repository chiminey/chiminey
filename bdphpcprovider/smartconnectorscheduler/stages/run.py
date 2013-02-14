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
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
#from bdphpcprovider.smartconnectorscheduler.sshconnector import \
#    find_remote_files, run_command, put_file, run_sudo_command_with_status
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_settings, \
    get_run_info, get_filesys, update_key, get_all_settings
from bdphpcprovider.smartconnectorscheduler import sshconnector

from bdphpcprovider.smartconnectorscheduler.stages.errors import BadSpecificationError


class Run(Stage):
    """
    Start application on nodes and return status
    """
    def __init__(self):
        self.numbfile = 0
        self.initial_numbfile = 1

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.
        # input_dir is assumed to be populated.

        logger.debug("Run stage triggered")
        logger.debug(__name__)

        self.settings = get_all_settings(context)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.iter_inputdir = "input_%s" % self.id
        else:
            self.id = 0
            self.iter_inputdir = "input"
        logger.debug("id = %s" % id)

        if 'group_id' in self.settings:
            self.group_id = self.settings['group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
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
        ssh = sshconnector.open_connection(ip_address=ip,
                              settings=settings)
        makefile_path = settings['PAYLOAD_DESTINATION']
        command = "cd %s; make %s" % (makefile_path, 'startrun')
        sshconnector.run_sudo_command_with_status(ssh, command, settings, instance_id)

        # run_command(ssh, "cd %s; ./%s >& %s &\
        # " % (os.path.join(settings['PAYLOAD_DESTINATION'],
        #                   settings['PAYLOAD_CLOUD_DIRNAME']),
        #      settings['COMPILE_FILE'], "output"))

        attempts = settings['RETRY_ATTEMPTS']
        logger.debug("checking for package start")
        #FIXME: remove following and instead use a specific MakeFile target to return pid
        for x in range(0, attempts):
            time.sleep(5)  # to give process enough time to start
            pids = sshconnector.get_package_pids(ssh, settings['COMPILE_FILE'])
            logger.debug("pids=%s" % pids)
            if pids:
                break
        else:
            raise PackageFailedError("package did not start")
        # pids should have maximum of one element
        return pids

    def run_task_old(self, instance_id, settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.info("run_task %s" % instance_id)
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = sshconnector.open_connection(ip_address=ip,
                              settings=settings)
        pids = sshconnector.get_package_pids(ssh, settings['COMPILE_FILE'])
        logger.debug("pids=%s" % pids)
        if len(pids) > 1:
            logger.error("warning:multiple packages running")
            raise PackageFailedError("multiple packages running")
        sshconnector.run_command(ssh, "cd %s; ./%s >& %s &\
        " % (os.path.join(settings['PAYLOAD_DESTINATION'],
                          settings['PAYLOAD_CLOUD_DIRNAME']),
             settings['COMPILE_FILE'], "output"))

        attempts = settings['RETRY_ATTEMPTS']
        logger.debug("checking for package start")
        for x in range(0, attempts):
            time.sleep(5)  # to give process enough time to start
            pids = sshconnector.get_package_pids(ssh, settings['COMPILE_FILE'])
            logger.debug("pids=%s" % pids)
            if pids:
                break
        else:
            raise PackageFailedError("package did not start")
        # pids should have maximum of one element
        return pids

    # def job_finished(instance_id, settings):
    #     """
    #         Return True if package job on instance_id has job_finished
    #     """
    #     ip = botocloudconnector.get_instance_ip(instance_id, settings)
    #     ssh = open_connection(ip_address=ip, settings=settings)
    #     pids = get_package_pids(ssh, settings['COMPILE_FILE'])
    #     logger.debug("pids=%s" % repr(pids))
    #     return pids == [""]

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

    def _expand_variations(self, template, maps, initial_numbfile, generator_counter):
        """
        Based on maps, generate all range variations from the template
        """
        # FIXME: doesn't handle multipe template files together
        res = []
        numbfile = initial_numbfile
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            logger.debug("iter #%d" % iter)
            temp_num = 0
            # ensure ordering of the template_map entries
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            for z in product(*map_ranges):
                context = {}
                for i, k in enumerate(map_keys):
                    context[k] = str(z[i])  # str() so that 0 doesn't default value
                #instance special variables into the template context
                context['run_counter'] = numbfile
                context['generator_counter'] = generator_counter
                numbfile += 1
                logger.debug(context)
                t = Template(template)
                con = Context(context)
                res.append((t.render(con), context))
                temp_num += 1
            logger.debug("%d files created" % (temp_num))
        return res

    def _upload_variation_inputs(self, variations, nodes, input_dir, fs):
        """
        Create input packages for each variation and upload the vms
        """
        logger.debug("variations = %s" % variations)
        # generate variations for the input_dir
        for var_fname in variations.keys():
            logger.debug("var_fname=%s" % var_fname)
            for var_content, values in variations[var_fname]:
                logger.debug("var_content = %s" % var_content)
                var_node = nodes[self.node_ind]
                self.node_ind += 1
                ip = botocloudconnector.get_instance_ip(var_node.id, self.settings)
                ssh = sshconnector.open_connection(ip_address=ip, settings=self.settings)

                # Cleanup any existing runs already there
                # get all files from the payload directory
                dest_files = sshconnector.find_remote_files(ssh,
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
                    sshconnector.run_command(ssh, "/bin/rm -f %s" % f)

                # first copy up all existing input files to new variation
                fs.upload_iter_input_dir(ssh, self.iter_inputdir, input_dir, os.path.join(
                    self.settings['PAYLOAD_DESTINATION'],
                    self.settings['PAYLOAD_CLOUD_DIRNAME']))

                # FIXME: handle exceptions

                # then create template variated file
                varied_fdir = tempfile.mkdtemp()
                logger.debug("varied_fdir=%s" % varied_fdir)
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
                sshconnector.put_file(ssh, varied_fdir, var_fname, os.path.join(
                    self.settings['PAYLOAD_DESTINATION'],
                    self.settings['PAYLOAD_CLOUD_DIRNAME']))
                sshconnector.put_file(ssh, varied_fdir, values_fname, os.path.join(
                    self.settings['PAYLOAD_DESTINATION'],
                    self.settings['PAYLOAD_CLOUD_DIRNAME']))

                # cleanup
                import shutil
                shutil.rmtree(varied_fdir)

    def _generate_variations(self, input_dir, fs, context):
        """
        For each templated file in input_dir, generate all variations
        """
        template_pat = re.compile("(.*)_template")

        variations = {}
        for fname in fs.get_local_subdirectory_files(self.iter_inputdir,
                input_dir):
            logger.debug("trying %s/%s/%s" % (self.iter_inputdir, input_dir,
                fname))
            data_object = fs.retrieve_under_dir(self.iter_inputdir, input_dir,
                fname)

            template_mat = template_pat.match(fname)
            if template_mat:
                # get the template
                template = data_object.retrieve()
                logger.debug("template content = %s" % template)

                base_fname = template_mat.group(1)
                logger.debug("base_fname=%s" % base_fname)

                # find assocaited values file and generator_counter
                generator_counter = 0
                try:
                    values_file = fs.retrieve_under_dir(self.iter_inputdir,
                        input_dir,
                        "%s_values" % base_fname)
                except IOError:
                    logger.warn("no values file found")
                else:

                    logger.debug("values_file=%s" % values_file)
                    values_content = values_file.retrieve()
                    logger.debug("values_content = %s" % values_content)
                    values_map = dict(json.loads(values_content))
                    logger.debug("values_map=%s" % values_map)
                    try:
                        generator_counter = values_map.get('run_counter')
                    except KeyError:
                        logger.warn("could not retrieve generator counter")

                num_dim = 1
                # variations map spectification
                if num_dim == 1:
                    N = context['number_vm_instances']
                    map = {
                        'temp': [300],
                        'iseed': [randrange(0, self.settings['MAX_SEED_INT'])
                            for x in xrange(0, N)],
                        'istart': [1 if self.id > 0 else 2]
                    }
                elif num_dim == 2:
                    self.threshold = context['threshold']
                    N = self.threshold[0]
                    map = {
                        'temp': [300],
                        'iseed': [randrange(0, self.settings['MAX_SEED_INT'])
                            for x in xrange(0, 4 * N)],
                        'istart': [2]

                    }
                    if self.id > 0:
                        map = {
                            'temp': [i for i in [300, 700, 1100, 1500]],
                            'iseed': [randrange(0,
                                self.settings['MAX_SEED_INT'])],
                            'istart': [1]

                            }
                else:
                    message = "Unknown dimensionality of problem"
                    logger.error(message)
                    raise BadSpecificationError(message)
                logger.debug("generator_counter= %s" % generator_counter)
                if not template_mat.groups():
                    logger.info("found odd template matching file %s" % fname)
                else:

                    # generates a set of variations for the template fname
                    variation_set = self._expand_variations(template,
                        [map], self.initial_numbfile, generator_counter)
                    self.initial_numbfile += len(variation_set)
                    variations[base_fname] = variation_set
                logger.debug("map=%s" % map)
        else:
            # normal file
            pass
        return variations

    def _prepare_inputs(self, context):
        """
        Upload all input files for this run
        """
        logger.debug("preparing inputs")
        fs = get_filesys(context)
        logger.debug("fs= %s GLobal %s" % (fs, fs.global_filesystem))

        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)

        # #get initial seed
        # # FIXME: this is domain specific code
        # if 'seed' in self.settings:
        #     seed = self.settings['seed']
        # else:
        #     seed = 42
        #     logger.warn("No seed specified. Using default value")

        # come in with N input directoires

        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
        self.node_ind = 0
        logger.debug("Iteration Inpt dir %s" % self.iter_inputdir)
        input_dirs = fs.get_local_subdirectories(self.iter_inputdir)
        for input_dir in input_dirs:
            logger.debug("Inpt dir %s" % input_dir)

            if not fs.isdir(self.iter_inputdir, input_dir):
                continue

            self._upload_variation_inputs(self._generate_variations(input_dir,
                                            fs, context), nodes, input_dir, fs)

    def process(self, context):

        logger.debug("processing run stage")

        self._prepare_inputs(context)
        logger.debug("running tasks")

        try:
            pids = self.run_multi_task(self.group_id, self.iter_inputdir, self.settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages: %s" % e)
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)
        return pids

    def output(self, context):
        """
        Assume that no nodes have finished yet and indicate to future stages
        """

        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)
        logger.debug("nodes = %s" % nodes)

        update_key('runs_left', len(nodes), context)

        return context
