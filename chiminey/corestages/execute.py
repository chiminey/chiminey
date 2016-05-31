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
from django.template import TemplateSyntaxError
from chiminey.smartconnectorscheduler import jobs
from chiminey.platform import manage
from chiminey.corestages import stage
from django.core.exceptions import ImproperlyConfigured
from chiminey.smartconnectorscheduler.errors import PackageFailedError, BadInputException
from chiminey.smartconnectorscheduler import models
from chiminey import storage
from chiminey import messages
from chiminey.sshconnection import open_connection
from chiminey.compute import run_make
from django.conf import settings as django_settings

from chiminey.runsettings import getval, setvals, getvals, update, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs, get_make_path


logger = logging.getLogger(__name__)


class Execute(stage.Stage):
    """
    Start application on nodes and return status
    """

    VALUES_FNAME = django_settings.VALUES_FNAME

    def __init__(self, user_settings=None):
        self.numbfile = 0
        logger.debug("Execute stage initialized")

    def is_triggered(self, run_settings):
        """
        Triggered when we now that we have N nodes setup and ready to run.
         input_dir is assumed to be populated.
        """
        try:
            schedule_completed = int(getval(
                run_settings, '%s/stages/schedule/schedule_completed' % django_settings.SCHEMA_PREFIX))
            self.all_processes = ast.literal_eval(
                getval(run_settings, '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX))

        except SettingNotFoundException, e:
            return False
        except ValueError, e:
            return False

        if not schedule_completed:
            return False
        try:
            scheduled_procs_str = getval(
                run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            return False
        try:
            self.schedule_procs = ast.literal_eval(scheduled_procs_str)
        except ValueError:
            return False

        if len(self.schedule_procs) == 0:
            return False
        try:
            self.reschedule_failed_procs = getval(
                run_settings, '%s/input/reliability/reschedule_failed_processes' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            self.reschedule_failed_procs = 0  # FIXME: check this is correct
        try:
            exec_procs_str = getval(
                run_settings, '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX)
            self.exec_procs = ast.literal_eval(exec_procs_str)
            logger.debug('executed procs=%d, scheduled procs = %d'
                         % (len(self.exec_procs), len(self.schedule_procs)))
            self.ready_processes = [
                x for x in self.schedule_procs if x['status'] == 'ready']
            logger.debug('ready_processes= %s' % self.ready_processes)
            logger.debug('total ready procs %d' % len(self.ready_processes))
            return len(self.ready_processes)
            # return len(self.exec_procs) < len(self.schedule_procs)
        except SettingNotFoundException, e:
            logger.debug(e)
            self.exec_procs = []
            return True
        return False

    def process(self, run_settings):
        try:
            self.rand_index = int(
                getval(run_settings, '%s/stages/run/rand_index' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            try:
                self.rand_index = int(
                    getval(run_settings, '%s/input/hrmc/iseed' % django_settings.SCHEMA_PREFIX))
            except SettingNotFoundException, e:
                self.rand_index = 42
                logger.debug(e)

        logger.debug("processing execute stage")
        local_settings = getvals(
            run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        self.set_execute_settings(run_settings, local_settings)

        self.contextid = getval(
            run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX)
        # NB: Don't catch SettingNotFoundException because we can't recover
        # run_settings['%s/system' % django_settings.SCHEMA_PREFIX][u'contextid']
        logger.debug('contextid=%s' % self.contextid)
        output_storage_url = getval(
            run_settings, '%s/platform/storage/output/platform_url' % django_settings.SCHEMA_PREFIX)
        output_storage_settings = manage.get_platform_settings(
            output_storage_url, local_settings['bdp_username'])
        offset = getval(
            run_settings, '%s/platform/storage/output/offset' % django_settings.SCHEMA_PREFIX)
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        # TODO: we assume initial input is in "%s/input_0" % self.job_dir
        # in configure stage we could copy initial data in 'input_location'
        # into this location
        try:
            self.id = int(getval(run_settings, '%s/system/id' %
                                 django_settings.SCHEMA_PREFIX))
            self.iter_inputdir = os.path.join(
                self.job_dir, "input_%s" % self.id)
        except (SettingNotFoundException, ValueError):
            self.id = 0
            self.iter_inputdir = os.path.join(self.job_dir, "input_location")
        messages.info(run_settings, "%s: Executing" % (self.id + 1))
        logger.debug("id = %s" % self.id)

        try:
            self.initial_numbfile = int(
                getval(run_settings, '%s/stages/run/initial_numbfile' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            logger.warn("setting initial_numbfile for first iteration")
            self.initial_numbfile = 1
        try:
            self.experiment_id = int(
                getval(run_settings, '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        logger.debug("process run_settings=%s" % pformat(run_settings))

        computation_platform_url = getval(
            run_settings, '%s/platform/computation/platform_url' % django_settings.SCHEMA_PREFIX)
        comp_pltf_settings = manage.get_platform_settings(
            computation_platform_url, local_settings['bdp_username'])
        if local_settings['curate_data']:
            mytardis_url = getval(
                run_settings, '%s/input/mytardis/mytardis_platform' % django_settings.SCHEMA_PREFIX)
            mytardis_settings = manage.get_platform_settings(
                mytardis_url, local_settings['bdp_username'])
        else:
            mytardis_settings = {}

        failed_processes = [
            x for x in self.schedule_procs if x['status'] == 'failed']
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
            # TODO: cleanup node of copied input files etc.
            sys.exit(1)

        return pids

    def _copy_previous_inputs(self, local_settings, output_storage_settings,
                              computation_platform_settings):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                      output_storage_settings['type'])
        for proc in self.ready_processes:
            source_location = os.path.join(
                self.job_dir, "input_backup", proc['id'])
            source_files_url = get_url_with_credentials(output_storage_settings,
                                                        output_prefix + source_location, is_relative_path=False)
            relative_path_suffix = self.get_relative_output_path(
                local_settings)
            #dest_files_location = computation_platform_settings['type'] + "@"\
            #                      + os.path.join(
            #    local_settings['payload_destination'],
            #    proc['id'], local_settings['process_output_dirname'])
            dest_files_location = computation_platform_settings['type'] + "@"\
                + os.path.join(relative_path_suffix,
                               proc['id'], local_settings['smart_connector_input'])
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
                '%s/stages/execute/executed_procs' % django_settings.SCHEMA_PREFIX: str(self.exec_procs),
                '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX: str(self.schedule_procs),
                '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX: str(self.all_processes)
                })

        #completed_processes = [x for x in self.exec_procs if x['status'] == 'completed']
        completed_processes = [
            x for x in self.schedule_procs if x['status'] == 'completed']
        running_processes = [
            x for x in self.schedule_procs if x['status'] == 'running']
        logger.debug('completed_processes=%d' % len(completed_processes))
        setvals(run_settings, {
                '%s/stages/run/runs_left' % django_settings.SCHEMA_PREFIX:
                    len(running_processes),

                    # len(self.exec_procs) - len(completed_processes),
                '%s/stages/run/initial_numbfile' % django_settings.SCHEMA_PREFIX: self.initial_numbfile,
                # fixme remove rand_index
                '%s/stages/run/rand_index' % django_settings.SCHEMA_PREFIX: self.rand_index,
                '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX: str(self.experiment_id)
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
        relative_path = settings['type'] + '@' + \
            os.path.join(relative_path_suffix, process_id)
        destination = get_url_with_credentials(settings,
                                               relative_path,
                                               is_relative_path=True,
                                               ip_address=ip_address)
        makefile_path = get_make_path(destination)
        try:
            ssh = open_connection(ip_address=ip_address, settings=settings)
            logger.debug(settings['process_output_dirname'])
            try:
                hadoop = run_settings['%s/input/system/compplatform/hadoop' % django_settings.SCHEMA_PREFIX]
                sudo = False
                options = "%s input_%s_%s output_%s_%s HADOOP_INPUT %s %s"  % (
                    settings['process_output_dirname'], self.contextid, process_id, self.contextid,
                    process_id, settings['hadoop_home_path'], self.get_optional_args(run_settings))
                command, errs = run_make(
                ssh, makefile_path,
                'start_running_process  %s'  % options,#, self.contextid, process_id),
            sudo= sudo
            )
            except KeyError:
                sudo = True
                command, errs = run_make(
                ssh, makefile_path,
                'start_running_process %s %s'  % (settings['smart_connector_input'],
                settings['process_output_dirname']), sudo= sudo)


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
        logger.debug('self.schedule_procs=%s' % self.schedule_procs)
        for proc in self.schedule_procs:
            if proc['status'] != 'ready':
                continue
            #instance_id = node.id
            ip_address = proc['ip_address']
            process_id = proc['id']
            try:
                pids_for_task = self.run_task(
                    ip_address, process_id, settings, run_settings)
                proc['status'] = 'running'
                # self.exec_procs.append(proc)
                for iterator, process in enumerate(self.all_processes):
                    if int(process['id']) == int(process_id) and process['status'] == 'ready':
                        self.all_processes[iterator]['status'] = 'running'
                        break
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package on node %s" % ip_address)
                # TODO: cleanup node of copied input files etc.
            except Exception, e:
                logger.debug('error=%s' % e)
                # fixme FT management
                pass
            else:
                pids.append(pids_for_task)
                logger.debug('pids=%s' % pids)
        #all_pids = dict(zip(nodes, pids))
        all_pids = pids
        logger.debug('all_pids=%s' % all_pids)
        return all_pids

    def _get_variation_contexts(self, run_maps, values_map, initial_numbfile):
        """
        Based on run_maps, generate all range variations from the template
        """
        contexts = []
        generator_counter = 0
        num_file = initial_numbfile
        try:
            generator_counter = values_map['run_counter']
        except KeyError:
            logger.warn("could not retrieve generator counter")
        for iter, run_map in enumerate(run_maps):
            logger.debug("run_map=%s" % run_map)
            logger.debug("iter #%d" % iter)
            temp_num = 0
            # ensure ordering of the run_map entries
            map_keys = run_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(run_map[x]) for x in map_keys]
            for z in product(*map_ranges):
                context = dict(values_map)
                for i, k in enumerate(map_keys):
                    # str() so that 0 doesn't default value
                    context[k] = str(z[i])
                # instance special variables into the template context
                context['run_counter'] = num_file
                # FIXME: not needed?
                context['generator_counter'] = generator_counter
                contexts.append(context)
                temp_num += 1
                num_file += 1
            logger.debug("%d contexts created" % (temp_num))
        return contexts

    def prepare_inputs(self, local_settings, output_storage_settings,
                       computation_platform_settings, mytardis_settings, run_settings):
        """
        Upload all input directories for this iteration
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

        input_dirs = list_dirs(url_with_pkey)
        if not input_dirs:
            raise BadInputException(
                "require an initial subdirectory of input directory")

        for input_dir in sorted(input_dirs):
            self._upload_input_dir_variations(processes,
                                              local_settings,
                                              computation_platform_settings,
                                              output_storage_settings, mytardis_settings,
                                              input_dir, run_settings)

    def _upload_input_dir_variations(self, processes, local_settings,
                                     computation_platform_settings,
                                     output_storage_settings,
                                     mytardis_settings,
                                     input_dir, run_settings):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                      output_storage_settings['type'])
        input_url_with_credentials = get_url_with_credentials(
            output_storage_settings, output_prefix + os.path.join(
                self.iter_inputdir, input_dir),
            is_relative_path=False)
        logger.debug('input_url_with_credentials=%s' %
                     input_url_with_credentials)
        if local_settings['curate_data']:

            try:
                mytardis_platform = jobs.safe_import('chiminey.platform.mytardis.MyTardisPlatform', [], {})
                self.experiment_id = mytardis_platform.create_dataset_for_input(self.experiment_id,
                                                      run_settings, local_settings,
                                                      output_storage_settings,
                                                      mytardis_settings,
                                                      input_url_with_credentials)
            except ImproperlyConfigured as  e:
                logger.error("Cannot load mytardis platform hook %s" % e)

        else:
            logger.warn('Data curation is off')

        # get run Map
        parent_stage = self.import_parent_stage(run_settings)
        run_map, self.rand_index = parent_stage.get_internal_sweep_map(local_settings,
                                                                       run_settings=run_settings)

        # load value_map
        values_url_with_pkey = get_url_with_credentials(
            output_storage_settings,
            output_prefix + os.path.join(self.iter_inputdir,
                                         input_dir,
                                         self.VALUES_FNAME),
            is_relative_path=False)
        logger.debug("initial values_file=%s" % values_url_with_pkey)
        values = {}
        try:
            values_content = storage.get_file(values_url_with_pkey)
        except IOError:
            logger.warn("no values file found")
        else:
            logger.debug("values_content = %s" % values_content)
            values = dict(json.loads(values_content))
        logger.debug("values=%s" % values)

        # generates a set of variations for the template fname
        contexts = self._get_variation_contexts(
            [run_map], values,  self.initial_numbfile)
        self.initial_numbfile += len(contexts)

        # for each context, copy each file to dest and any
        # templates to be instantiated, then store in values.

        template_pat = re.compile("(.*)_template")
        relative_path_suffix = self.get_relative_output_path(local_settings)

        for context in contexts:
            logger.debug("context=%s" % context)
            # get list of all files in input_dir
            fname_url_with_pkey = get_url_with_credentials(
                output_storage_settings,
                output_prefix + os.path.join(self.iter_inputdir, input_dir),
                is_relative_path=False)
            input_files = storage.list_dirs(fname_url_with_pkey,
                                            list_files=True)

            # get process information
            run_counter = context['run_counter']
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
                raise BadInputException()
            logger.debug("proc=%s" % pformat(proc))

            for fname in input_files:
                logger.debug("fname=%s" % fname)
                templ_mat = template_pat.match(fname)
                fname_url_with_credentials = storage.get_url_with_credentials(
                    output_storage_settings,
                    output_prefix +
                    os.path.join(self.iter_inputdir, input_dir, fname),
                    is_relative_path=False)
                logger.debug("fname_url_with_credentials=%s" %
                             fname_url_with_credentials)

                def put_dest_file(proc, fname,
                                  dest_file_location, resched_file_location,
                                  content):
                    dest_url = get_url_with_credentials(
                        computation_platform_settings, os.path.join(
                            dest_file_location, fname),
                        is_relative_path=True, ip_address=proc['ip_address'])
                    logger.debug("writing to =%s" % dest_url)
                    #logger.debug("content=%s" % content)
                    storage.put_file(dest_url, content)
                    if self.reschedule_failed_procs:
                        logger.debug("resched=%s" % resched_file_location)
                        logger.debug("fname=%s" % fname)
                        logger.debug("output_storage_settings=%s" %
                                     output_storage_settings)

                        logger.debug("here")
                        test = "%s/%s" % (resched_file_location, fname)
                        logger.debug("test=%s" % test)
                        resched_url = get_url_with_credentials(
                            output_storage_settings, test)
                        logger.debug("writing backup to %s" % resched_url)
                        storage.put_file(resched_url, content)
                    logger.debug("done")

                outputs = []
                if templ_mat:
                    base_fname = templ_mat.group(1)
                    template_content = storage.get_file(
                        fname_url_with_credentials)
                    try:
                        templ = Template(template_content)
                    except TemplateSyntaxError, e:
                        logger.error(e)
                        # FIXME: should detect this during submission of job,
                        # as no sensible way to recover here.
                        # TODO: signal error conditions in job status
                        continue
                    new_context = Context(context)
                    logger.debug("new_content=%s" % new_context)
                    render_output = templ.render(new_context)
                    render_output = render_output.encode('utf-8')
                    outputs.append((base_fname, render_output))
                    outputs.append((fname, template_content))

                else:
                    content = storage.get_file(fname_url_with_credentials)
                    outputs.append((fname, content))

                for (new_fname, content) in outputs:
                    dest_file_location = computation_platform_settings['type']\
                        + "@" + os.path.join(relative_path_suffix,
                                             proc['id'],
                                             local_settings['smart_connector_input'])
                    if computation_platform_settings['type'] == 'hadoop':
                        dest_file_location = os.path.join(dest_file_location, 'HADOOP_INPUT')

                    logger.debug("dest_file_location =%s" % dest_file_location)
                    resched_file_location = "%s%s" % (output_prefix, os.path.join(
                        self.job_dir, "input_backup", proc['id']))

                    logger.debug("resched_file_location=%s" %
                                 resched_file_location)
                    put_dest_file(proc, new_fname, dest_file_location,
                                  resched_file_location, content)

            # then copy context new values file
            logger.debug("writing values file")
            values_dest_location = computation_platform_settings['type']\
                + "@" + os.path.join(relative_path_suffix,
                                     proc['id'],
                                     local_settings['smart_connector_input'],
                                     self.VALUES_FNAME)
            logger.debug("values_dest_location =%s" % values_dest_location)

            values_dest_url = get_url_with_credentials(
                computation_platform_settings, values_dest_location,
                is_relative_path=True, ip_address=proc['ip_address'])

            storage.put_file(values_dest_url, json.dumps(context, indent=4))

        logger.debug("done input upload")

    def set_execute_settings(self, run_settings, local_settings):
        self.set_domain_settings(run_settings, local_settings)
        update(local_settings, run_settings,
               '%s/stages/setup/payload_destination' % django_settings.SCHEMA_PREFIX,
               '%s/stages/setup/filename_for_PIDs' % django_settings.SCHEMA_PREFIX,
               '%s/stages/setup/process_output_dirname' % django_settings.SCHEMA_PREFIX,
               '%s/stages/setup/smart_connector_input' % django_settings.SCHEMA_PREFIX,
               '%s/system/contextid' % django_settings.SCHEMA_PREFIX,
               '%s/system/random_numbers' % django_settings.SCHEMA_PREFIX,
               '%s/system/id' % django_settings.SCHEMA_PREFIX

               )
        try:
            local_settings['curate_data'] = getval(run_settings,
                                                   '%s/input/mytardis/curate_data' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            local_settings['curate_data'] = 0
        local_settings['bdp_username'] = getval(run_settings,
                                                '%s/bdp_userprofile/username' % django_settings.SCHEMA_PREFIX)
        if '%s/input/system/compplatform/hadoop' % django_settings.SCHEMA_PREFIX in run_settings.keys():
            from chiminey.platform import get_platform_settings
            platform_url = run_settings['%s/platform/computation' % django_settings.SCHEMA_PREFIX]['platform_url']
            pltf_settings = get_platform_settings(platform_url, local_settings['bdp_username'])
            local_settings['root_path'] = '/home/%s' % pltf_settings['username']
            local_settings['hadoop_home_path'] = pltf_settings['hadoop_home_path']
            logger.debug('root_path=%s' % local_settings['root_path'])
        else:
            logger.debug('root_path not found')


    #def curate_data(self, experiment_id, local_settings, output_storage_settings,
    #                mytardis_settings, source_files_url):
    #    return self.experiment_id

    def set_domain_settings(self, run_settings, local_settings):
         try:
             schema = models.Schema.objects.get(namespace=self.get_input_schema_namespace(
                run_settings['%s/directive_profile' % django_settings.SCHEMA_PREFIX]['directive_name']))
             if schema:
                params = models.ParameterName.objects.filter(schema=schema)
                if params:
                    namespace = schema.namespace
                    domain_params = [os.path.join(namespace, i.name) for i in params]
                    update(local_settings, run_settings, *domain_params)
         except models.Schema.DoesNotExist:
             pass


    def get_optional_args(self, run_settings):
        from os.path import basename
        namespace = self.get_input_schema_namespace(
            run_settings['%s/directive_profile' % django_settings.SCHEMA_PREFIX]['directive_name'])
        try:
            args_keys = django_settings.SMART_CONNECTORS[basename(namespace)]['args']
        except KeyError:
            args_keys = []
        args = ''
        for i in args_keys:
            try:
                args = '%s %s' % (args, run_settings[namespace][i])
                logger.debug('args=%s' % args)
            except KeyError:
                logger.debug('Failed to find key %s' % i)
                pass
        logger.debug('optional_args_keys=%s' % args)
        return args
