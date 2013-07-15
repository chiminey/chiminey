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
import ast
import time
import logging
import logging.config
import json
import re
import tempfile
from itertools import product
from pprint import pformat
from urlparse import urlparse, parse_qsl

from django.template import Context, Template

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import deprecated
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadSpecificationError, BadInputException
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import mytardis


logger = logging.getLogger(__name__)


class Run(Stage):
    """
    Start application on nodes and return status
    """
    def __init__(self, user_settings=None):
        self.numbfile = 0

        self.job_dir = "hrmcrun"
        logger.debug("Run stage initialized")

    def triggered(self, run_settings):
        """
        Triggered when we now that we have N nodes setup and ready to run.
         input_dir is assumed to be populated.
        """

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/create', u'group_id'):
            self.group_id = run_settings[
                'http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
        logger.debug("group_id = %s" % self.group_id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/deploy', u'deployed_nodes'):
            deployed_nodes = ast.literal_eval(str(run_settings[
                'http://rmit.edu.au/schemas/stages/deploy'][
                u'deployed_nodes']))
        else:
            return False
        logger.debug("deployed_nodes=%s" % deployed_nodes)

        try:
            number_vm_instances = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        except KeyError:
            logger.error("no number_vm_instances found in context")
            return False

        logger.debug("number_vm_instances=%s" % number_vm_instances)

        if len(deployed_nodes) == number_vm_instances:

            logger.debug("deployed_nodes = %s" % deployed_nodes)

            if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
                run_settings['http://rmit.edu.au/schemas/stages/run'] = {}
            if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
                logger.debug("found runs_left")
                return False
            return True

        logger.info("setup was not finished")
        return False

    def run_task(self, instance_id, settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.info("run_task %s" % instance_id)
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        logger.debug("ip=%s" % ip)
        curr_username = settings['username']
        settings['username'] = 'root'
        # ssh = sshconnector.open_connection(ip_address=ip,
        #                                    settings=settings)
        # settings['username'] = curr_username

        relative_path = settings['platform'] + '@' + settings['payload_destination']
        destination = smartconnector.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip)
        makefile_path = get_make_path(destination)
        #makefile_path = settings['payload_destination']
        command = "cd %s; make %s" % (makefile_path, 'startrun')

        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip)
        try:
            ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
            command_out, errs = sshconnector.run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))

        # #sshconnector.run_sudo_command_with_status(ssh, command, settings, instance_id)

        # command_out, _ = sshconnector.run_command_with_status(ssh, command)

        # # run_command(ssh, "cd %s; ./%s >& %s &\
        # # " % (os.path.join(settings['PAYLOAD_DESTINATION'],
        # #                   settings['PAYLOAD_CLOUD_DIRNAME']),
        # #      settings['COMPILE_FILE'], "output"))

        # attempts = settings['retry_attempts']
        # logger.debug("checking for package start")
        # #FIXME: remove following and instead use a specific MakeFile target to return pid
        # for x in range(0, attempts):
        #     time.sleep(5)  # to give process enough time to start
        #     pids = sshconnector.get_package_pids(ssh, settings['compile_file'])
        #     logger.debug("pids=%s" % pids)
        #     if pids:
        #         break
        # else:
        #     raise PackageFailedError("package did not start")
        #     # pids should have maximum of one element
        # return pids

    @deprecated
    def run_task_old(self, instance_id, settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.info("run_task %s" % instance_id)
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = sshconnector.open_connection(ip_address=ip,
                                           settings=settings)
        pids = sshconnector.get_package_pids(ssh, settings['compile_file'])
        logger.debug("pids=%s" % pids)
        if len(pids) > 1:
            logger.error("warning:multiple packages running")
            raise PackageFailedError("multiple packages running")
        sshconnector.run_command(ssh, "cd %s; ./%s >& %s &\
        " % (os.path.join(settings['payload_destination'],
                          settings['payload_cloud_dirname']),
             settings['compile_file'], "output"))

        attempts = settings['retry_attempts']
        logger.debug("checking for package start")
        for x in range(0, attempts):
            time.sleep(5)  # to give process enough time to start
            pids = sshconnector.get_package_pids(ssh, settings['compile_file'])
            logger.debug("pids=%s" % pids)
            if pids:
                break
        else:
            raise PackageFailedError("package did not start")
            # pids should have maximum of one element
        return pids

    def run_multi_task(self, group_id, iter_inputdir, settings):
        """
        Run the package on each of the nodes in the group and grab
        any output as needed
        """
        nodes = botocloudconnector.get_rego_nodes(group_id, settings)
        pids = []
        for node in nodes:
            instance_id = node.id
            try:
                pids_for_task = self.run_task(instance_id, settings)
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package on node %s" % node)
                #TODO: cleanup node of copied input files etc.
            else:
                pids.append(pids_for_task)
        all_pids = dict(zip(nodes, pids))
        return all_pids

    def _expand_variations(self, template, maps, values, initial_numbfile):
        """
        Based on maps, generate all range variations from the template
        """
        # FIXME: doesn't handle multipe template files together
        logger.debug("values=%s" % values)
        res = []
        generator_counter = 0
        numbfile = initial_numbfile
        try:
            generator_counter = values['run_counter']
        except KeyError:
            logger.warn("could not retrieve generator counter")
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            logger.debug("iter #%d" % iter)
            temp_num = 0
            # ensure ordering of the template_map entries
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            for z in product(*map_ranges):
                context = dict(values)
                for i, k in enumerate(map_keys):
                    context[k] = str(z[i])  # str() so that 0 doesn't default value
                #instance special variables into the template context
                context['run_counter'] = numbfile
                context['generator_counter'] = generator_counter  # FIXME: not needed?

                numbfile += 1
                #logger.debug(context)
                t = Template(template)
                con = Context(context)
                res.append((t.render(con), context))
                temp_num += 1
            logger.debug("%d files created" % (temp_num))
        return res

    def _upload_variation_inputs(self, variations, nodes, input_dir):
        '''
        Create input packages for each variation and upload the vms
        '''
        #logger.debug("variations = %s" % variations)
        # generate variations for the input_dir

        source_files_url = smartconnector.get_url_with_pkey(self.boto_settings,
                                                  os.path.join(self.iter_inputdir,
                                                               input_dir), is_relative_path=False)
        logger.debug('source_files_url=%s' % source_files_url)

        # Copy input directory to mytardis only after saving locally, so if
        # something goes wrong we still have the results
        if self.boto_settings['mytardis_host']:

            self.experiment_id = mytardis.post_dataset(
                settings=self.boto_settings,
                source_url=source_files_url,
                exp_id=self.experiment_id,
                exp_name=_get_exp_name_for_input,
                dataset_name=_get_dataset_name_for_input,
                dataset_schema="http://rmit.edu.au/schemas/hrmcdataset/input")
        else:
            logger.warn("no mytardis host specified")

        for var_fname in variations.keys():
            logger.debug("var_fname=%s" % var_fname)
            for var_content, values in variations[var_fname]:
                #logger.debug("var_content = %s" % var_content)
                var_node = nodes[self.node_ind]
                self.node_ind += 1
                ip = botocloudconnector.get_instance_ip(var_node.id, self.boto_settings)

                dest_files_location = self.boto_settings['platform'] + "@"\
                                      + os.path.join(self.boto_settings['payload_destination'],
                                                     self.boto_settings['payload_cloud_dirname'])
                logger.debug('dest_files_location=%s' % dest_files_location)

                dest_files_url = smartconnector.get_url_with_pkey(self.boto_settings, dest_files_location,
                                       is_relative_path=True, ip_address=ip)
                logger.debug('dest_files_url=%s' % dest_files_url)

                # FIXME: Cleanup any existing runs already there
                # FIXME: keep the compile exec from setup
                #FIXME: exceptions should be given as parameter
                exceptions = [self.boto_settings['compile_file'], "..", ".",
                              'PSD', 'PSD.f', 'PSD_exp.dat', 'PSD.inp']
                hrmcstages.delete_files(dest_files_url, exceptions=exceptions)
                hrmcstages.copy_directories(source_files_url, dest_files_url)

                # # then create template variated file
                # from bdphpcprovider.smartconnectorscheduler import models
                # platform_object = models.Platform.objects.get(name='local')
                # root_path = platform_object.root_path

                # sysTemp = tempfile.gettempdir()
                # myTemp = os.path.join(sysTemp, root_path, self.job_dir)
                # varied_fdir = tempfile.mkdtemp(suffix='foo', prefix='bar', dir=myTemp)

                # Why do we need to create a tempory file to make this copy?
                import uuid
                randsuffix = unicode(uuid.uuid4())  # should use some job id here

                var_url = smartconnector.get_url_with_pkey(self.boto_settings, os.path.join("tmp%s" % randsuffix, "var"),
                    is_relative_path=True)
                logger.debug("var_url=%s" % var_url)
                hrmcstages.put_file(var_url, var_content.encode('utf-8'))

                value_url = smartconnector.get_url_with_pkey(self.boto_settings, os.path.join("tmp%s" % randsuffix, "value"),
                    is_relative_path=True)
                logger.debug("value_url=%s" % value_url)
                hrmcstages.put_file(value_url, json.dumps(values))

                # #varied_fdir = tempfile.mkdtemp()
                # logger.debug("varied_fdir=%s" % varied_fdir)
                # fpath = os.path.join(varied_fdir, var_fname)
                # f = open(fpath, "w")
                # f.write(var_content)
                # f.close()

                # # plus store used val in substitution incase next iter needs them.
                #values_fname = "%s_values" % var_fname
                # vpath = os.path.join(varied_fdir, values_fname)
                # v = open(vpath, "w")
                # v.write(json.dumps(values))
                # v.close()

                # tmp_dir_basename = os.path.basename(varied_fdir)
                # var_url = 'file://localhost/%s/%s?root_path=%s' % (tmp_dir_basename, var_fname, root_path)
                # var_content = hrmcstages.get_file(var_url)
                # values_url = 'file://localhost/%s/%s?root_path=%s' % (tmp_dir_basename, values_fname, root_path)
                # values_content = hrmcstages.get_file(values_url)

                # and overwrite on the remote
                var_fname_remote = self.boto_settings['platform']\
                    + "@" + os.path.join(self.boto_settings['payload_destination'],
                                         self.boto_settings['payload_cloud_dirname'],
                                         var_fname)
                var_fname_pkey = smartconnector.get_url_with_pkey(self.boto_settings, var_fname_remote,
                                                        is_relative_path=True, ip_address=ip)
                var_content = hrmcstages.get_file(var_url)
                hrmcstages.put_file(var_fname_pkey, var_content)
                logger.debug("var_fname_pkey=%s" % var_fname_pkey)
                values_fname_pkey = smartconnector.get_url_with_pkey(self.boto_settings,
                                                           os.path.join(dest_files_location,
                                                                        "%s_values" % var_fname),
                                                           is_relative_path=True, ip_address=ip)
                values_content = hrmcstages.get_file(value_url)
                hrmcstages.put_file(values_fname_pkey, values_content)
                logger.debug("values_fname_pkey=%s" % values_fname_pkey)
                # cleanup

                tmp_url = smartconnector.get_url_with_pkey(self.boto_settings, os.path.join("tmp%s" % randsuffix),
                    is_relative_path=True)
                logger.debug("deleting %s" % tmp_url)
                #hrmcstages.delete_files(url)

    def _generate_variations(self, input_dir, run_settings):
        """
        For each templated file in input_dir, generate all variations
        """
        template_pat = re.compile("(.*)_template")

        fname_url_with_pkey = smartconnector.get_url_with_pkey(
            self.boto_settings,
            os.path.join(self.iter_inputdir, input_dir),
            is_relative_path=False)
        input_files = hrmcstages.list_dirs(fname_url_with_pkey,
            list_files=True)

        variations = {}
        # TODO: only tested with single template file per input
        for fname in input_files:
            logger.debug("trying %s/%s/%s" % (self.iter_inputdir, input_dir,
                                              fname))

            template_mat = template_pat.match(fname)
            if template_mat:
                # get the template
                basename_url_with_pkey = smartconnector.get_url_with_pkey(
                    self.boto_settings,
                    os.path.join(self.iter_inputdir, input_dir, fname),
                    is_relative_path=False)
                template = hrmcstages.get_file(basename_url_with_pkey)

                base_fname = template_mat.group(1)
                logger.debug("base_fname=%s" % base_fname)

                # find assocaited values file and generator_counter
                values_map = {}
                try:
                    values_url_with_pkey = smartconnector.get_url_with_pkey(
                        self.boto_settings,
                        os.path.join(self.iter_inputdir,
                            input_dir,
                            '%s_values' % base_fname),
                        is_relative_path=False)

                    logger.debug("values_file=%s" % values_url_with_pkey)
                    values_content = hrmcstages.get_file(values_url_with_pkey)
                except IOError:
                    logger.warn("no values file found")
                else:

                    #logger.debug("values_file=%s" % values_url_with_pkey)
                    #values_content = hrmcstages.get_file(values_url_with_pkey)
                    logger.debug("values_content = %s" % values_content)
                    values_map = dict(json.loads(values_content))

                    # TODO: rather than loading up specific vars for info
                    # to send to next set of variations, pass whole values_map
                    # and then override with map.  This means we need no
                    # special variables here, could easily propogate values
                    # between iterations and we might also pass an list
                    # of values...

                num_dim = run_settings['number_dimensions']
                # variations map spectification
                if 'pottype' in run_settings:
                    logger.debug("pottype=%s" % run_settings['pottype'])
                    try:
                        pottype = int(run_settings['pottype'])
                    except ValueError:
                        logger.error("cannot convert %s to pottype" % run_settings['pottype'])
                        pottype = 0
                else:
                    pottype = 0

                if num_dim == 1:

                    N = run_settings['number_vm_instances']

                    rand_nums = hrmcstages.generate_rands(run_settings,
                        0, self.boto_settings['max_seed_int'],
                        N, self.rand_index)
                    self.rand_index += N

                    map = {
                        'temp': [300],
                        'iseed': rand_nums,
                        'istart': [1 if self.id > 0 else 2],
                        'pottype': [pottype]
                    }
                elif num_dim == 2:
                    self.threshold = run_settings['threshold']
                    logger.debug("threshold=%s" % self.threshold)
                    N = int(ast.literal_eval(self.threshold)[0])
                    logger.debug("N=%s" % N)
                    if not self.id:

                        rand_nums = hrmcstages.generate_rands(run_settings,
                           0, self.boto_settings['max_seed_int'],
                           4 * N, self.rand_index)
                        self.rand_index += N
                        map = {
                            'temp': [300],
                            'iseed': rand_nums,
                            'istart': [2],
                            'pottype': [pottype],
                        }
                    else:
                        rand_nums = hrmcstages.generate_rands(run_settings,
                            0, self.boto_settings['max_seed_int'],
                            1, self.rand_index)
                        self.rand_index += N
                        map = {
                            'temp': [i for i in [300, 700, 1100, 1500]],
                            'iseed': rand_nums,
                            'istart': [1],
                            'pottype': [pottype],

                        }
                else:
                    message = "Unknown dimensionality of problem"
                    logger.error(message)
                    raise BadSpecificationError(message)
                if not template_mat.groups():
                    logger.info("found odd template matching file %s" % fname)
                else:

                    # generates a set of variations for the template fname
                    variation_set = self._expand_variations(template,
                                                            [map], values_map,  self.initial_numbfile)
                    self.initial_numbfile += len(variation_set)
                    variations[base_fname] = variation_set
                logger.debug("map=%s" % map)
        else:
            # normal file
            pass
        logger.debug('Variations %s' % variations)
        return variations




    def _prepare_inputs(self):
        """
        Upload all input files for this run
        """
        logger.debug("preparing inputs")

        # TODO: to ensure reproducability, may want to precalculate all random numbers and
        # store rather than rely on canonical execution of rest of this funciton.
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

        nodes = sorted(botocloudconnector.get_rego_nodes(self.group_id, self.boto_settings))
        self.node_ind = 0
        logger.debug("Iteration Input dir %s" % self.iter_inputdir)
        url_with_pkey = smartconnector.get_url_with_pkey(self.boto_settings, self.iter_inputdir, is_relative_path=False)
        logger.debug("url_with_pkey=%s" % url_with_pkey)
        input_dirs = hrmcstages.list_dirs(url_with_pkey)
        if not input_dirs:
            raise BadInputException("require an initial subdirectory of input directory")
        for input_dir in sorted(input_dirs):
            logger.debug("Input dir %s" % input_dir)
            self._upload_variation_inputs(self._generate_variations(input_dir, self.boto_settings),
                                          nodes, input_dir)

    def process(self, run_settings):

        logger.debug("processing run stage")

        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        #TODO: we assume relative path BDP_URL here, but could be made to work with non-relative (ie., remote paths)
        self.job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']

        # TODO: we assume initial input is in "%s/input_0" % self.job_dir
        # in configure stage we could copy initial data in 'input_location' into this location
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.iter_inputdir = os.path.join(self.job_dir, "input_%s" % self.id)
        else:
            # FIXME: not fully tested
            self.id = 0
            self.iter_inputdir = os.path.join(self.job_dir, "input_location")

        # if 'id' in self.boto_settings:
        #     self.id = self.boto_settings['id']
        #     #self.iter_inputdir = "input_%s" % self.id
        #     self.iter_inputdir = self.boto_settings['input_location'] + "_%s" % self.id
        # else:
        #     self.id = 0
        #     #self.iter_inputdir = "input"
        #     self.iter_inputdir = self.boto_settings['input_location']
        logger.debug("id = %s" % self.id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'initial_numbfile'):
            self.initial_numbfile = run_settings['http://rmit.edu.au/schemas/stages/run'][u'initial_numbfile']
        else:
            logger.warn("setting initial_numbfile for first iteration")
            self.initial_numbfile = 1

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'rand_index'):
            self.rand_index = run_settings['http://rmit.edu.au/schemas/stages/run'][u'rand_index']
        else:
            logger.warn("setting rand_index for first iteration")
            self.rand_index = run_settings['http://rmit.edu.au/schemas/hrmc']['iseed']
        logger.debug("rand_index=%s" % self.rand_index)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/hrmc', u'experiment_id'):
            try:
                self.experiment_id = int(run_settings['http://rmit.edu.au/schemas/hrmc'][u'experiment_id'])
            except ValueError, e:
                self.experiment_id = 0
        else:
            self.experiment_id = 0

        logger.debug("run_settings=%s" % run_settings)

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
            'http://rmit.edu.au/schemas/stages/create/created_nodes')
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
            'http://rmit.edu.au/schemas/hrmc/pottype')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/random_numbers')
        self.boto_settings['username'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['username'] = 'root'  # FIXME: schema value is ignored

        self.boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
        key_file = hrmcstages.retrieve_private_key(self.boto_settings,
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nectar_private_key'])
        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file

        self._prepare_inputs()
        try:
            pids = self.run_multi_task(self.group_id, self.iter_inputdir,
                                       self.boto_settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages: %s" % e)
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)

        return pids

    def output(self, run_settings):
        """
        Assume that no nodes have finished yet and indicate to future stages
        """
        nodes = botocloudconnector.get_rego_nodes(self.group_id, self.boto_settings)
        logger.debug("nodes = %s" % nodes)

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
            run_settings['http://rmit.edu.au/schemas/stages/run'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left'] = len(nodes)
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'initial_numbfile'] = self.initial_numbfile
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'rand_index'] = self.rand_index
        run_settings['http://rmit.edu.au/schemas/hrmc']['experiment_id'] = str(self.experiment_id)

        return run_settings


def get_make_path(destination):
    """
    TODO: move this into hrmcstages?
    """
    destination = hrmcstages.get_http_url(destination)
    url = urlparse(destination)
    query = parse_qsl(url.query)
    query_settings = dict(x[0:] for x in query)
    path = url.path
    if path[0] == os.path.sep:
        path = path[1:]
    make_path = os.path.join(query_settings['root_path'], path)
    logger.debug("Makefile path %s %s %s " % (make_path, query_settings['root_path'], path))
    return make_path


EXP_DATASET_NAME_SPLIT = 2


def _get_exp_name_for_input(settings, url, path):
    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))


def _get_dataset_name_for_input(settings, url, path):
    logger.debug("path=%s" % path)

    source_url = smartconnector.get_url_with_pkey(
        settings, os.path.join(path, "HRMC.inp_values"),
        is_relative_path=True)
    logger.debug("source_url=%s" % source_url)
    try:
        content = hrmcstages.get_file(source_url)
    except IOError:
        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

    logger.debug("content=%s" % content)
    try:
        values_map = dict(json.loads(str(content)))
    except Exception, e:
        logger.warn("cannot load %s: %s" % (content, e))
        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

    try:
        iteration = str(path.split(os.sep)[-2:-1][0])
    except Exception, e:
        logger.error(e)
        iteration = ""

    if "_" in iteration:
        iteration = iteration.split("_")[1]
    else:
        iteration = "initial"

    if 'run_counter' in values_map:
        run_counter = values_map['run_counter']
    else:
        run_counter = 0

    dataset_name = "%s_%s" % (iteration,
        run_counter)
    logger.debug("dataset_name=%s" % dataset_name)
    return dataset_name
