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

import sys
import os
import ast
from pprint import pformat
import logging
import json
import re
from itertools import product

from django.template import Context, Template
from chiminey.platform import manage
from chiminey.corestages import stage

from chiminey.smartconnectorscheduler.errors import PackageFailedError
from chiminey.smartconnectorscheduler.stages.errors import BadInputException
from chiminey.smartconnectorscheduler import models
from chiminey import storage
from chiminey import messages
from chiminey.sshconnection import open_connection
from chiminey.compute import run_make

from chiminey.runsettings import getval, setvals, getvals, update, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs, get_make_path


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Execute(stage.Stage):
    """
    Start application on nodes and return status
    """
    def __init__(self, user_settings=None):
        self.numbfile = 0
        logger.debug("Execute stage initialized")

    def is_triggered(self, run_settings):
        """
        Triggered when we now that we have N nodes setup and ready to run.
         input_dir is assumed to be populated.
        """
        try:
            schedule_completed = int(getval(run_settings, '%s/stages/schedule/schedule_completed' % RMIT_SCHEMA))
            # schedule_completed = int(smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/stages/schedule/schedule_completed'))

            self.all_processes = ast.literal_eval(getval(run_settings, '%s/stages/schedule/all_processes' % RMIT_SCHEMA))
            # self.all_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/stages/schedule/all_processes'))

        except SettingNotFoundException, e:
            return False
        except ValueError, e:
            return False

        if not schedule_completed:
            return False
        try:
            scheduled_procs_str = getval(run_settings, '%s/stages/schedule/current_processes' % RMIT_SCHEMA)
            # scheduled_procs_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
        except SettingNotFoundException:
            return False
        try:
            self.schedule_procs = ast.literal_eval(scheduled_procs_str)
        except ValueError:
            return False

        if len(self.schedule_procs) == 0:
            return False
        try:
            self.reschedule_failed_procs = getval(run_settings, '%s/input/reliability/reschedule_failed_processes' % RMIT_SCHEMA)
        except SettingNotFoundException:
            self.reschedule_failed_procs = 0  # FIXME: check this is correct
        try:
            exec_procs_str = getval(run_settings, '%s/stages/execute/executed_procs' % RMIT_SCHEMA)
            # exec_procs_str = smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/stages/execute/executed_procs')
            self.exec_procs = ast.literal_eval(exec_procs_str)
            logger.debug('executed procs=%d, scheduled procs = %d'
                         % (len(self.exec_procs), len(self.schedule_procs)))
            self.ready_processes = [x for x in self.schedule_procs if x['status'] == 'ready']
            logger.debug('ready_processes= %s' % self.ready_processes)
            logger.debug('total ready procs %d' % len(self.ready_processes))
            return len(self.ready_processes)
            #return len(self.exec_procs) < len(self.schedule_procs)
        except SettingNotFoundException, e:
            logger.debug(e)
            self.exec_procs = []
            return True
        return False

    def process(self, run_settings):
        try:
            self.rand_index = int(getval(run_settings, '%s/stages/run/rand_index' % RMIT_SCHEMA))
        except SettingNotFoundException:
            try:
                self.rand_index = int(getval(run_settings, '%s/input/hrmc/iseed' % RMIT_SCHEMA))
            except SettingNotFoundException, e:
                self.rand_index = 42
                logger.debug(e)

        logger.debug("processing execute stage")
        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        #self.retrieve_boto_settings(run_settings, local_settings)
        self.set_execute_settings(run_settings, local_settings)


        self.contextid = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)
        # NB: Don't catch SettingNotFoundException because we can't recover
        # run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        output_storage_url = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
        output_storage_settings = manage.get_platform_settings(output_storage_url, local_settings['bdp_username'])
        offset = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
        # offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        # TODO: we assume initial input is in "%s/input_0" % self.job_dir
        # in configure stage we could copy initial data in 'input_location' into this location
        try:
            self.id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
            self.iter_inputdir = os.path.join(self.job_dir, "input_%s" % self.id)
        except (SettingNotFoundException, ValueError):
            self.id = 0
            self.iter_inputdir = os.path.join(self.job_dir, "input_location")
        messages.info(run_settings, "%s: execute" % (self.id + 1))
        logger.debug("id = %s" % self.id)

        try:
            self.initial_numbfile = int(getval(run_settings, '%s/stages/run/initial_numbfile' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            logger.warn("setting initial_numbfile for first iteration")
            self.initial_numbfile = 1
        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
            # self.experiment_id = int(smartconnector.get_existing_key(run_settings,
            #     'http://rmit.edu.au/schemas/input/mytardis/experiment_id'))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        logger.debug("process run_settings=%s" % pformat(run_settings))

        computation_platform_url = getval(run_settings, '%s/platform/computation/platform_url' % RMIT_SCHEMA)
        comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
        if local_settings['curate_data']:
            mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
            mytardis_settings = manage.get_platform_settings(mytardis_url, local_settings['bdp_username'])
        else:
            mytardis_settings = {}


        #generic_output_schema = 'http://rmit.edu.au/schemas/platform/storage/output'

        failed_processes = [x for x in self.schedule_procs if x['status'] == 'failed']
        if self.input_exists(run_settings):
            if not failed_processes:
                self.prepare_inputs(
                    local_settings, output_storage_settings, comp_pltf_settings, mytardis_settings, run_settings)
            else:
                self._copy_previous_inputs(
                    local_settings, output_storage_settings,
                    comp_pltf_settings)
        try:
            local_settings.update(comp_pltf_settings)
            pids = self.run_multi_task(local_settings, run_settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages: %s" % e)
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)

        return pids

    def _copy_previous_inputs(self, local_settings, output_storage_settings,
                              computation_platform_settings):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        for proc in self.ready_processes:
            source_location = os.path.join(self.job_dir, "input_backup", proc['id'])
            source_files_url = get_url_with_credentials(output_storage_settings,
                    output_prefix + source_location, is_relative_path=False)
            relative_path_suffix = self.get_relative_output_path(local_settings)
            #dest_files_location = computation_platform_settings['type'] + "@"\
            #                      + os.path.join(
            #    local_settings['payload_destination'],
            #    proc['id'], local_settings['payload_cloud_dirname'])
            dest_files_location = computation_platform_settings['type'] + "@"\
                                  + os.path.join(relative_path_suffix,
                proc['id'], local_settings['payload_cloud_dirname'])
            logger.debug('dest_files_location=%s' % dest_files_location)

            dest_files_url = get_url_with_credentials(
                computation_platform_settings, dest_files_location,
                is_relative_path=True, ip_address=proc['ip_address'])
            logger.debug('dest_files_url=%s' % dest_files_url)
            storage.copy_directories(source_files_url, dest_files_url)

    def output(self, run_settings):
        """
        Assume that no nodes have finished yet and indicate to future corestages
        """

        setvals(run_settings, {
                '%s/stages/execute/executed_procs' % RMIT_SCHEMA: str(self.exec_procs),
                '%s/stages/schedule/current_processes' % RMIT_SCHEMA: str(self.schedule_procs),
                '%s/stages/schedule/all_processes' % RMIT_SCHEMA: str(self.all_processes)
                })

        #completed_processes = [x for x in self.exec_procs if x['status'] == 'completed']
        completed_processes = [x for x in self.schedule_procs if x['status'] == 'completed']
        running_processes = [x for x in self.schedule_procs if x['status'] == 'running']
        logger.debug('completed_processes=%d' % len(completed_processes))
        setvals(run_settings, {
                '%s/stages/run/runs_left' % RMIT_SCHEMA:
                    len(running_processes),

                    # len(self.exec_procs) - len(completed_processes),
                '%s/stages/run/initial_numbfile' % RMIT_SCHEMA: self.initial_numbfile,
                '%s/stages/run/rand_index' % RMIT_SCHEMA: self.rand_index, #fixme remove rand_index
                '%s/input/mytardis/experiment_id' % RMIT_SCHEMA: str(self.experiment_id)
                })
        return run_settings

    def run_task(self, ip_address, process_id, settings, run_settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.debug("run_task %s" % ip_address)
        #ip = botocloudconnector.get_instance_ip(instance_id, settings)
        #ip = ip_address
        logger.debug("ip=%s" % ip_address)
        # curr_username = settings['username']
        #settings['username'] = 'root'
        # ssh = sshconnector.open_connection(ip_address=ip,
        #                                    settings=settings)
        # settings['username'] = curr_username

        #relative_path = settings['type'] + '@' + settings['payload_destination'] + "/" + process_id
        relative_path_suffix = self.get_relative_output_path(settings)
        relative_path = settings['type'] + '@' + os.path.join(relative_path_suffix, process_id)
        destination = get_url_with_credentials(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip_address)
        makefile_path = get_make_path(destination)
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            command, errs = run_make(ssh, makefile_path, 'start_running_process')
            logger.debug('execute_command=%s' % command
            )
        finally:
            ssh.close()

    def run_multi_task(self, settings, run_settings):
        """
        Run the package on each of the nodes in the group and grab
        any output as needed
        """
        pids = []
        logger.debug('exec_procs=%s' % self.exec_procs)
        tmp_exec_procs = []
        for iterator, proc in enumerate(self.exec_procs):
            if proc['status'] != 'failed':
                tmp_exec_procs.append(proc)
                logger.debug('adding=%s' % proc)
            else:
                logger.debug('not adding=%s' % proc)
        self.exec_procs = tmp_exec_procs
        logger.debug('exec_procs=%s' % self.exec_procs)
        for proc in self.schedule_procs:
            if proc['status'] != 'ready':
                continue
            #instance_id = node.id
            ip_address = proc['ip_address']
            process_id = proc['id']
            try:
                pids_for_task = self.run_task(ip_address, process_id, settings, run_settings)
                proc['status'] = 'running'
                #self.exec_procs.append(proc)
                for iterator, process in enumerate(self.all_processes):
                    if int(process['id']) == int(process_id) and process['status'] == 'ready':
                        self.all_processes[iterator]['status'] = 'running'
                        break
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package on node %s" % ip_address)
                #TODO: cleanup node of copied input files etc.
            except Exception:
                #fixme FT management
                pass
            else:
                pids.append(pids_for_task)
        #all_pids = dict(zip(nodes, pids))
        all_pids = pids
        logger.debug('all_pids=%s' % all_pids)
        return all_pids

    def prepare_inputs(self, local_settings, output_storage_settings,
                        computation_platform_settings, mytardis_settings, run_settings):
        """
        Upload all input files for this run
        """
        logger.debug("preparing inputs")
        # TODO: to ensure reproducability, may want to precalculate all random numbers and
        # store rather than rely on canonical execution of rest of this funciton.
        #processes = self.schedule_procs
        processes = [x for x in self.schedule_procs
                    if x['status'] == 'ready']
        self.node_ind = 0
        logger.debug("Iteration Input dir %s" % self.iter_inputdir)
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                output_storage_settings['type'])
        url_with_pkey = get_url_with_credentials(
            output_storage_settings, output_prefix + self.iter_inputdir, is_relative_path=False)
        logger.debug("url_with_pkey=%s" % url_with_pkey)
        input_dirs = list_dirs(url_with_pkey)
        if not input_dirs:
            raise BadInputException("require an initial subdirectory of input directory")
        for input_dir in sorted(input_dirs):
            logger.debug("Input dir %s" % input_dir)
            self.upload_variation_inputs(
                run_settings, local_settings, self.generate_variations(
                    input_dir, local_settings, output_storage_settings, run_settings),
                processes, input_dir, output_storage_settings,
                computation_platform_settings, mytardis_settings)

    def generate_variations(self, input_dir, local_settings, output_storage_settings, run_settings):
        """
        For each templated file in input_dir, generate all variations
        """
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        template_pat = re.compile("(.*)_template")
        fname_url_with_pkey = get_url_with_credentials(
            output_storage_settings,
            output_prefix + os.path.join(self.iter_inputdir, input_dir),
            is_relative_path=False)
        input_files = storage.list_dirs(fname_url_with_pkey,
            list_files=True)

        variations = {}
        # TODO: only tested with single template file per input
        parent_stage = self.import_parent_stage(run_settings)

        for fname in input_files:
            logger.debug("trying %s/%s/%s" % (self.iter_inputdir, input_dir,
                                              fname))
            template_mat = template_pat.match(fname)
            if template_mat:
                # get the template
                basename_url_with_pkey = get_url_with_credentials(
                    output_storage_settings,
                    output_prefix + os.path.join(self.iter_inputdir, input_dir, fname),
                    is_relative_path=False)
                template = storage.get_file(basename_url_with_pkey)
                base_fname = template_mat.group(1)
                logger.debug("base_fname=%s" % base_fname)

                # find associated values file and generator_counter
                values_map = {}
                try:
                    values_url_with_pkey = get_url_with_credentials(
                        output_storage_settings,
                        output_prefix + os.path.join(self.iter_inputdir,
                            input_dir,
                            '%s_values' % base_fname),
                        is_relative_path=False)

                    logger.debug("values_file=%s" % values_url_with_pkey)
                    values_content = storage.get_file(values_url_with_pkey)
                except IOError:
                    logger.warn("no values file found")
                else:
                    logger.debug("values_content = %s" % values_content)
                    values_map = dict(json.loads(values_content))

                    # TODO: rather than loading up specific vars for info
                    # to send to next set of variations, pass whole values_map
                    # and then override with map.  This means we need no
                    # special variables here, could easily propogate values
                    # between iterations and we might also pass an list
                    # of values...

                map, self.rand_index = parent_stage.get_run_map(local_settings,
                                       run_settings=run_settings)

                if not template_mat.groups():
                    logger.info("found odd template matching file %s" % fname)
                else:

                    logger.debug("self.initial_numbfile=%s" % self.initial_numbfile)
                    # generates a set of variations for the template fname
                    variation_set = self._expand_variations(template,
                                                            [map], values_map,  self.initial_numbfile)
                    self.initial_numbfile += len(variation_set)
                    logger.debug('variation_set=%d' % len(variation_set))
                    logger.debug("self.initial_numbfile=%s" % self.initial_numbfile)
                    variations[base_fname] = variation_set
                logger.debug("map=%s" % map)
        else:
            # normal file
            pass
        logger.debug('Variations %s' % variations)
        logger.debug("Variations items %d" % len(variations.items()))
        return variations


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
                    logger.debug("context=%s" % context)
                    numbfile += 1
                    #logger.debug(context)
                    t = Template(template)
                    con = Context(context)

                    res.append((t.render(con), context))
                    temp_num += 1
                logger.debug("%d files created" % (temp_num))
            return res

    def curate_data(self, experiment_id, local_settings, output_storage_settings,
                    mytardis_settings, source_files_url):
        return self.experiment_id

    def upload_variation_inputs(self, run_settings, local_settings, variations, processes,
                                 input_dir, output_storage_settings,
                                 computation_platform_settings, mytardis_settings):
        '''
        Create input packages for each variation and upload the vms
        '''
        logger.debug("upload_variation_inputs")
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        source_files_url = get_url_with_credentials(
            output_storage_settings, output_prefix + os.path.join(
                self.iter_inputdir, input_dir),
            is_relative_path=False)

        logger.debug('source_files_url=%s' % source_files_url)
        # Copy input directory to mytardis only after saving locally, so if
        # something goes wrong we still have the results
        if local_settings['curate_data']:
            self.experiment_id = self.curate_data(self.experiment_id, local_settings, output_storage_settings,
                             mytardis_settings, source_files_url)
        else:
            logger.warn('Data curation is off')
        #proc_ind = 0
        for var_fname in variations.keys():
            logger.debug("var_fname=%s" % var_fname)
            logger.debug('variations[var_fname]=%s' % variations[var_fname])
            for var_content, values in variations[var_fname]:
                #logger.debug("var_content = %s" % var_content)
                #logger.debug('proc_ind=%s' % proc_ind)
                logger.debug('processes=%s' % processes)
                run_counter = values['run_counter']
                logger.debug("run_counter=%s" % run_counter)
                proc = None
                for p in processes:
                    # TODO: how to handle invalid run_counter
                    pid = int(p['id'])
                    logger.debug("pid=%s" % pid)
                    if pid == run_counter:
                        proc = p
                        break
                else:
                    logger.error("no process found matching run_counter")
                    #smartconnector.error(run_settings, "%s: wait" % (self.id + 1))
                    # TODO: catch this error and recover
                    raise BadInputException()

                logger.debug("proc=%s" % pformat(proc))

                #proc = processes[proc_ind]
                #proc_ind += 1
                #ip = botocloudconnector.get_instance_ip(var_node.id, local_settings)
                ip = proc['ip_address']

                #dest_files_location = computation_platform_settings['type'] + "@"\
                #                      + os.path.join(local_settings['payload_destination'],
                #                                     proc['id'],
                #                                     local_settings['payload_cloud_dirname']
                #                                     )
                relative_path_suffix = self.get_relative_output_path(local_settings)
                dest_files_location = computation_platform_settings['type'] + "@"\
                                      + os.path.join(relative_path_suffix,
                                                     proc['id'],
                                                     local_settings['payload_cloud_dirname']
                                                     )

                logger.debug('dest_files_location=%s' % dest_files_location)

                dest_files_url = get_url_with_credentials(
                    computation_platform_settings, dest_files_location,
                    is_relative_path=True, ip_address=ip)
                logger.debug('dest_files_url=%s' % dest_files_url)

                # FIXME: Cleanup any existing runs already there
                # FIXME: keep the compile exec from setup
                #FIXME: exceptions should be given as parameter
                #FIXme we should not delete anyfile. SInce each process runs in its own directory
                exceptions = [local_settings['compile_file'], "..", ".",
                              'PSD', 'PSD.f', 'PSD_exp.dat', 'PSD.inp',
                              'Makefile', 'running.sh',
                              'process_scheduledone.sh', 'process_schedulestart.sh']
                storage.copy_directories(source_files_url, dest_files_url)

                if self.reschedule_failed_procs:
                    input_backup = os.path.join(self.job_dir, "input_backup", proc['id'])
                    backup_url = get_url_with_credentials(
                        output_storage_settings,
                        output_prefix + input_backup, is_relative_path=False)
                    storage.copy_directories(source_files_url, backup_url)

                # Why do we need to create a tempory file to make this copy?
                import uuid
                randsuffix = unicode(uuid.uuid4())  # should use some job id here

                var_url = get_url_with_credentials(local_settings, os.path.join("tmp%s" % randsuffix, "var"),
                    is_relative_path=True)
                logger.debug("var_url=%s" % var_url)
                storage.put_file(var_url, var_content.encode('utf-8'))

                value_url = get_url_with_credentials(local_settings, os.path.join("tmp%s" % randsuffix, "value"),
                    is_relative_path=True)
                logger.debug("value_url=%s" % value_url)
                storage.put_file(value_url, json.dumps(values))

                #local_settings['platform'] should be replaced
                # and overwrite on the remote
                #var_fname_remote = computation_platform_settings['type']\
                #    + "@" + os.path.join(local_settings['payload_destination'],
                #                         proc['id'],
                #                         local_settings['payload_cloud_dirname'],
                #                         var_fname)
                var_fname_remote = computation_platform_settings['type']\
                    + "@" + os.path.join(relative_path_suffix,
                                         proc['id'],
                                         local_settings['payload_cloud_dirname'],
                                         var_fname)

                var_fname_pkey = get_url_with_credentials(
                    computation_platform_settings, var_fname_remote,
                    is_relative_path=True, ip_address=ip)
                var_content = storage.get_file(var_url)
                storage.put_file(var_fname_pkey, var_content)

                logger.debug("var_fname_pkey=%s" % var_fname_pkey)
                values_fname_pkey = get_url_with_credentials(
                    computation_platform_settings,
                    os.path.join(dest_files_location,
                                 "%s_values" % var_fname),
                    is_relative_path=True, ip_address=ip)
                values_content = storage.get_file(value_url)
                storage.put_file(values_fname_pkey, values_content)
                logger.debug("values_fname_pkey=%s" % values_fname_pkey)

                #copying values and var_content to backup folder
                if self.reschedule_failed_procs:
                    value_url = get_url_with_credentials(
                        output_storage_settings,
                        output_prefix + os.path.join(input_backup, "%s_values" % var_fname),
                        is_relative_path=False)
                    logger.debug("value_url=%s" % value_url)
                    storage.put_file(value_url, json.dumps(values))

                    var_fname_pkey = get_url_with_credentials(
                        output_storage_settings,
                        output_prefix + os.path.join(input_backup, var_fname),
                        is_relative_path=False)
                    var_content = storage.get_file(var_url)
                    storage.put_file(var_fname_pkey, var_content)

                # cleanup
                tmp_url = get_url_with_credentials(local_settings, os.path.join("tmp%s" % randsuffix),
                    is_relative_path=True)
                logger.debug("deleting %s" % tmp_url)

    def set_execute_settings(self, run_settings, local_settings):
        self.set_domain_settings(run_settings, local_settings)
        update(local_settings, run_settings,
               '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
               '%s/stages/setup/filename_for_PIDs' % RMIT_SCHEMA,
               '%s/stages/run/payload_cloud_dirname' % RMIT_SCHEMA,
               '%s/stages/run/compile_file' % RMIT_SCHEMA,
               '%s/stages/run/retry_attempts' % RMIT_SCHEMA,
               '%s/system/contextid' % RMIT_SCHEMA,
               '%s/system/random_numbers' % RMIT_SCHEMA,
               '%s/system/id' % RMIT_SCHEMA
        )
        try:
            local_settings['curate_data'] = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
        except SettingNotFoundException:
            local_settings['curate_data'] = 0
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA )



