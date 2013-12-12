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
from pprint import pformat
import logging
import json
import re

from itertools import product
from django.template import Context, Template
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler \
    import mytardis, models, hrmcstages, sshconnector, smartconnector, platform

from bdphpcprovider.smartconnectorscheduler.stages.composite import (make_graph_paramset, make_paramset)


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

class Execute(Stage):
    """
    Start application on nodes and return status
    """
    def __init__(self, user_settings=None):
        self.numbfile = 0
        self.job_dir = "hrmcrun"
        logger.debug("Execute stage initialized")


    def triggered(self, run_settings):
        """
        Triggered when we now that we have N nodes setup and ready to run.
         input_dir is assumed to be populated.
        """
        try:
            schedule_completed = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/schedule_completed'))
            self.all_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/all_processes'))
        except KeyError, e:
            logger.error(e)
            return False
        if not schedule_completed:
            return False
        scheduled_procs_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
        self.schedule_procs = ast.literal_eval(scheduled_procs_str)
        if len(self.schedule_procs) == 0:
            return False

        self.reschedule_failed_procs = run_settings['http://rmit.edu.au/schemas/input/reliability'][u'reschedule_failed_processes']

        try:
            logger.debug('here i am')
            exec_procs_str = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/execute/executed_procs')
            self.exec_procs = ast.literal_eval(exec_procs_str)
            logger.debug('here i am again' )
            logger.debug('executed procs=%d, scheduled procs = %d'
                         % (len(self.exec_procs), len(self.schedule_procs)))
            self.ready_processes = [x for x in self.schedule_procs if x['status'] == 'ready']
            logger.debug('ready_processes= %s' % self.ready_processes)
            logger.debug('total ready procs %d' % len(self.ready_processes))
            return len(self.ready_processes)
            #return len(self.exec_procs) < len(self.schedule_procs)
        except KeyError, e:
            logger.debug(e)
            self.exec_procs = []
            return True
        return False


    def process(self, run_settings):

        logger.debug("processing execute stage")
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        retrieve_boto_settings(run_settings, local_settings)

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']
        output_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['platform_url']
        output_storage_settings = platform.get_platform_settings(output_storage_url, local_settings['bdp_username'])
        self.job_dir = platform.get_job_dir(output_storage_settings, run_settings)
        # TODO: we assume initial input is in "%s/input_0" % self.job_dir
        # in configure stage we could copy initial data in 'input_location' into this location
        try:
            self.id = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/system/id'))
            self.iter_inputdir = os.path.join(self.job_dir, "input_%s" % self.id)
        except KeyError, e:
            self.id = 0
            self.iter_inputdir = os.path.join(self.job_dir, "input_location")
        smartconnector.info(run_settings, "%s: execute" % (self.id + 1))
        logger.debug("id = %s" % self.id)
        try:
            self.initial_numbfile = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/run/initial_numbfile'))
        except KeyError:
            logger.warn("setting initial_numbfile for first iteration")
            self.initial_numbfile = 1

        try:
            self.rand_index = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/run/rand_index'))
        except KeyError:
            logger.warn("setting rand_index for first iteration")
            self.rand_index = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/input/hrmc/iseed'))
        logger.debug("rand_index=%s" % self.rand_index)

        try:
            self.experiment_id = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/input/mytardis/experiment_id'))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        logger.debug("process run_settings=%s" % pformat(run_settings))

        computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
        comp_pltf_settings = platform.get_platform_settings(computation_platform_url, local_settings['bdp_username'])

        mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
        mytardis_settings = platform.get_platform_settings(mytardis_url, local_settings['bdp_username'])

        #generic_output_schema = 'http://rmit.edu.au/schemas/platform/storage/output'

        failed_processes = [x for x in self.schedule_procs if x['status'] == 'failed']
        if not failed_processes:
            self._prepare_inputs(
                local_settings, output_storage_settings, comp_pltf_settings, mytardis_settings)
        else:
            self._copy_previous_inputs(
                local_settings, output_storage_settings,
                comp_pltf_settings)
        try:
            local_settings.update(comp_pltf_settings)
            pids = self.run_multi_task(local_settings)
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
            source_files_url = smartconnector.get_url_with_pkey(output_storage_settings,
                    output_prefix+source_location, is_relative_path=False)

            dest_files_location = computation_platform_settings['type'] + "@"\
                                  + os.path.join(
                local_settings['payload_destination'],
                proc['id'], local_settings['payload_cloud_dirname'])
            logger.debug('dest_files_location=%s' % dest_files_location)

            dest_files_url = smartconnector.get_url_with_pkey(
                computation_platform_settings, dest_files_location,
                is_relative_path=True, ip_address=proc['ip_address'])
            logger.debug('dest_files_url=%s' % dest_files_url)
            hrmcstages.copy_directories(source_files_url, dest_files_url)


    def output(self, run_settings):
        """
        Assume that no nodes have finished yet and indicate to future stages
        """
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/execute',
            {})[u'executed_procs'] = str(self.exec_procs)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'current_processes'] = str(self.schedule_procs)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'all_processes'] = str(self.all_processes)

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
            run_settings['http://rmit.edu.au/schemas/stages/run'] = {}

        completed_processes = [x for x in self.exec_procs if x['status'] == 'completed']
        logger.debug('completed_processes=%d' % len(completed_processes))
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left'] =\
            len(self.exec_procs) - len(completed_processes)
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'initial_numbfile'] = self.initial_numbfile
        run_settings['http://rmit.edu.au/schemas/stages/run'][u'rand_index'] = self.rand_index
        run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] = str(self.experiment_id)

        return run_settings


    def run_task(self, ip_address, process_id, settings):
        """
            Start the task on the instance, then hang and
            periodically check its state.
        """
        logger.info("run_task %s" % ip_address)
        #ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ip = ip_address
        logger.debug("ip=%s" % ip)
        curr_username = settings['username']
        settings['username'] = 'root'
        # ssh = sshconnector.open_connection(ip_address=ip,
        #                                    settings=settings)
        # settings['username'] = curr_username

        relative_path = settings['type'] + '@' + settings['payload_destination'] + "/" + process_id
        destination = smartconnector.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip)
        makefile_path = hrmcstages.get_make_path(destination)
        #makefile_path = settings['payload_destination']
        command = "cd %s; make -f Makefile %s" % (makefile_path, 'startrun IDS=%s' % (
                                      settings['filename_for_PIDs']))
        logger.debug('command_exec=%s' % command)
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


    def run_multi_task(self, settings):
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
                pids_for_task = self.run_task(ip_address, process_id, settings)
                proc['status'] = 'running'
                self.exec_procs.append(proc)
                for iterator, process in enumerate(self.all_processes):
                    if int(process['id']) == int(process_id) and process['status'] == 'ready':
                        self.all_processes[iterator]['status'] = 'running'
                        break
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start package on node %s" % ip_address)
                #TODO: cleanup node of copied input files etc.
            else:
                pids.append(pids_for_task)
        #all_pids = dict(zip(nodes, pids))
        all_pids = pids
        logger.debug('all_pids=%s' % all_pids)
        return all_pids


    def _prepare_inputs(self, local_settings, output_storage_settings,
                        computation_platform_settings, mytardis_settings):
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
            url_with_pkey = smartconnector.get_url_with_pkey(
                output_storage_settings, output_prefix+self.iter_inputdir, is_relative_path=False)
            logger.debug("url_with_pkey=%s" % url_with_pkey)
            input_dirs = hrmcstages.list_dirs(url_with_pkey)
            if not input_dirs:
                raise BadInputException("require an initial subdirectory of input directory")
            for input_dir in sorted(input_dirs):
                logger.debug("Input dir %s" % input_dir)
                self._upload_variation_inputs(
                    local_settings, self._generate_variations(
                        input_dir, local_settings, output_storage_settings),
                    processes, input_dir,output_storage_settings,
                    computation_platform_settings, mytardis_settings)


    def _generate_variations(self, input_dir, local_settings, output_storage_settings):
        """
        For each templated file in input_dir, generate all variations
        """
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        template_pat = re.compile("(.*)_template")
        fname_url_with_pkey = smartconnector.get_url_with_pkey(
            output_storage_settings,
            output_prefix+os.path.join(self.iter_inputdir, input_dir),
            is_relative_path=False)
        input_files = hrmcstages.list_dirs(fname_url_with_pkey,
            list_files=True)

        variations = {}
        # TODO: only tested with single template file per input
        # TODO: child_package should be link to current class not hardcoded
        child_package = "bdphpcprovider.smartconnectorscheduler.stages.execute.Execute"
        parent_stage = hrmcstages.get_parent_stage(child_package, local_settings)

        for fname in input_files:
            logger.debug("trying %s/%s/%s" % (self.iter_inputdir, input_dir,
                                              fname))
            template_mat = template_pat.match(fname)
            if template_mat:
                # get the template
                basename_url_with_pkey = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix + os.path.join(self.iter_inputdir, input_dir, fname),
                    is_relative_path=False)
                template = hrmcstages.get_file(basename_url_with_pkey)
                base_fname = template_mat.group(1)
                logger.debug("base_fname=%s" % base_fname)

                # find associated values file and generator_counter
                values_map = {}
                try:
                    values_url_with_pkey = smartconnector.get_url_with_pkey(
                        output_storage_settings,
                        output_prefix + os.path.join(self.iter_inputdir,
                            input_dir,
                            '%s_values' % base_fname),
                        is_relative_path=False)

                    logger.debug("values_file=%s" % values_url_with_pkey)
                    values_content = hrmcstages.get_file(values_url_with_pkey)
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
                                       rand_index=self.rand_index)

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
                    logger.debug("context=%s"% context)
                    numbfile += 1
                    #logger.debug(context)
                    t = Template(template)
                    con = Context(context)

                    res.append((t.render(con), context))
                    temp_num += 1
                logger.debug("%d files created" % (temp_num))
            return res

    def _upload_variation_inputs(self, local_settings, variations, processes,
                                 input_dir, output_storage_settings,
                                 computation_platform_settings, mytardis_settings):
        '''
        Create input packages for each variation and upload the vms
        '''
        logger.debug("upload_variation_inputs")
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        output_host = output_storage_settings['host']
        source_files_url = smartconnector.get_url_with_pkey(
            output_storage_settings, output_prefix + os.path.join(
                self.iter_inputdir, input_dir),
            is_relative_path=False)

        logger.debug('source_files_url=%s' % source_files_url)
        #file://127.0.0.1/sweephrmc261/hrmcrun262/input_0/initial
        #file://127.0.0.1/sweephrmc261/hrmcrun262/input_0/initial?root_path=/var/cloudenabling/remotesys
        # Copy input directory to mytardis only after saving locally, so if
        # something goes wrong we still have the results

        if mytardis_settings['mytardis_host']:
            EXP_DATASET_NAME_SPLIT = 2

            def _get_exp_name_for_input(settings, url, path):
                return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

            def _get_dataset_name_for_input(settings, url, path):
                logger.debug("path=%s" % path)

                source_url = smartconnector.get_url_with_pkey(
                    output_storage_settings,
                    output_prefix+os.path.join(output_host, path, "HRMC.inp_values"),
                    is_relative_path=False)
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

            # FIXME: better to create experiment_paramsets
            # later closer to when corresponding datasets are created, but
            # would required PUT of paramerset data to existing experiment.
            #fixme uncomment later
            local_settings.update(mytardis_settings)
            self.experiment_id = mytardis.post_dataset(
                settings=local_settings,
                source_url=source_files_url,
                exp_id=self.experiment_id,
                exp_name=_get_exp_name_for_input,
                dataset_name=_get_dataset_name_for_input,
                experiment_paramset=[],
                dataset_paramset=[
                    make_paramset('hrmcdataset/input', [])])

        else:
            logger.warn("no mytardis host specified")

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

                dest_files_location = computation_platform_settings['type'] + "@"\
                                      + os.path.join(local_settings['payload_destination'],
                                                     proc['id'],
                                                     local_settings['payload_cloud_dirname']
                                                     )
                logger.debug('dest_files_location=%s' % dest_files_location)

                dest_files_url = smartconnector.get_url_with_pkey(
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
                #hrmcstages.delete_files(dest_files_url, exceptions=exceptions) #FIXme: uncomment as needed
                hrmcstages.copy_directories(source_files_url, dest_files_url)

                if self.reschedule_failed_procs:
                    input_backup = os.path.join(self.job_dir, "input_backup", proc['id'])
                    backup_url = smartconnector.get_url_with_pkey(
                        output_storage_settings,
                        output_prefix+input_backup, is_relative_path=False)
                    hrmcstages.copy_directories(source_files_url, backup_url)

                # Why do we need to create a tempory file to make this copy?
                import uuid
                randsuffix = unicode(uuid.uuid4())  # should use some job id here

                var_url = smartconnector.get_url_with_pkey(local_settings, os.path.join("tmp%s" % randsuffix, "var"),
                    is_relative_path=True)
                logger.debug("var_url=%s" % var_url)
                hrmcstages.put_file(var_url, var_content.encode('utf-8'))

                value_url = smartconnector.get_url_with_pkey(local_settings, os.path.join("tmp%s" % randsuffix, "value"),
                    is_relative_path=True)
                logger.debug("value_url=%s" % value_url)
                hrmcstages.put_file(value_url, json.dumps(values))


                #local_settings['platform'] should be replaced
                # and overwrite on the remote
                var_fname_remote = computation_platform_settings['type']\
                    + "@" + os.path.join(local_settings['payload_destination'],
                                         proc['id'],
                                         local_settings['payload_cloud_dirname'],
                                         var_fname)
                var_fname_pkey = smartconnector.get_url_with_pkey(
                    computation_platform_settings, var_fname_remote,
                    is_relative_path=True, ip_address=ip)
                var_content = hrmcstages.get_file(var_url)
                hrmcstages.put_file(var_fname_pkey, var_content)


                logger.debug("var_fname_pkey=%s" % var_fname_pkey)
                values_fname_pkey = smartconnector.get_url_with_pkey(
                    computation_platform_settings,
                    os.path.join(dest_files_location,
                                 "%s_values" % var_fname),
                    is_relative_path=True, ip_address=ip)
                values_content = hrmcstages.get_file(value_url)
                hrmcstages.put_file(values_fname_pkey, values_content)
                logger.debug("values_fname_pkey=%s" % values_fname_pkey)

                #copying values and var_content to backup folder
                if self.reschedule_failed_procs:
                    value_url = smartconnector.get_url_with_pkey(
                        output_storage_settings,
                        output_prefix+os.path.join(input_backup, "%s_values" % var_fname),
                        is_relative_path=False)
                    logger.debug("value_url=%s" % value_url)
                    hrmcstages.put_file(value_url, json.dumps(values))

                    var_fname_pkey = smartconnector.get_url_with_pkey(
                        output_storage_settings,
                        output_prefix+os.path.join(input_backup, var_fname),
                        is_relative_path=False)
                    var_content = hrmcstages.get_file(var_url)
                    hrmcstages.put_file(var_fname_pkey, var_content)

                # cleanup
                tmp_url = smartconnector.get_url_with_pkey(local_settings, os.path.join("tmp%s" % randsuffix),
                    is_relative_path=True)
                logger.debug("deleting %s" % tmp_url)
                #hrmcstages.delete_files(u


def retrieve_boto_settings(run_settings, local_settings):
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_destination')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/filename_for_PIDs')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/platform')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/custom_prompt')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/max_seed_int')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/run/compile_file')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/run/retry_attempts')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/system/cloud/number_vm_instances')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/iseed')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/threshold')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/pottype')

    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/random_numbers')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/threshold')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/input/hrmc/pottype')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/max_seed_int')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/random_numbers')
    smartconnector.copy_settings(local_settings, run_settings,
        'http://rmit.edu.au/schemas/system/id')
    local_settings['bdp_username'] = run_settings[
        RMIT_SCHEMA + '/bdp_userprofile']['username']

    logger.debug('retrieve completed %s' % pformat(local_settings))
