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

import logging
import ast
import os

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler \
    import hrmcstages, models, smartconnector, sshconnector


logger = logging.getLogger(__name__)


class Wait(Stage):
    """
        Return whether the run has finished or not
    """

    def __init__(self, user_settings=None):
        self.runs_left = 0
        self.error_nodes = 0
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        logger.debug("Wait stage initialised")

    def triggered(self, run_settings):
        """
            Checks whether there is a non-zero number of runs still going.
        """
        try:
            executed_procs_str = run_settings['http://rmit.edu.au/schemas/stages/execute'][u'executed_procs']
            self.executed_procs = ast.literal_eval(executed_procs_str)
        except KeyError, e:
            logger.debug(e)
            return False

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/create', u'group_id'):
            self.group_id = run_settings['http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
        logger.debug("group_id = %s" % self.group_id)

        self.all_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/all_processes'))

        self.current_processes = ast.literal_eval(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/schedule/current_processes'))


        self.exec_procs = ast.literal_eval(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/execute/executed_procs'))

        if len(self.current_processes) == 0:
            return False

        # if we have no runs_left then we must have finished all the runs
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
            return run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left']

        return False

    def job_finished(self, ip_address, process_id, settings):
        """
            Return True if package job on instance_id has job_finished
        """
        ip = ip_address
        logger.debug("ip=%s" % ip)
        curr_username = settings['username']
        settings['username'] = 'root'
        relative_path = settings['platform'] + '@' + settings['payload_destination'] + "/" + process_id
        destination = smartconnector.get_url_with_pkey(settings,
            relative_path,
            is_relative_path=True,
            ip_address=ip)
        makefile_path = hrmcstages.get_make_path(destination)
        #makefile_path = settings['payload_destination']
        command = "cd %s; make %s" % (makefile_path, 'running') # IDS=%s' % (
                                      #settings['filename_for_PIDs']))

        command_out = ''
        errs = ''
        logger.debug("starting command for %s" % ip)
        logger.debug('command=%s' % command)
        try:
            ssh = sshconnector.open_connection(ip_address=ip, settings=settings)
            command_out, errs = sshconnector.run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))

        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if "stopped" in line:
                    return True
        #return True  # FIXME: this may be undesirable
        return False

    def get_output(self, ip_address, process_id, output_dir, settings):
        """
            Retrieve the output from the task on the node
        """
        logger.info("get_output of process %s on %s" % (process_id, ip_address))

        cloud_path = os.path.join(self.boto_settings['payload_destination'],
                                  process_id,
                                  self.boto_settings['payload_cloud_dirname']
                                  )
        logger.debug("cloud_path=%s" % cloud_path)
        logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
        ip = ip_address#botocloudconnector.get_instance_ip(instance_id, settings)
        #ssh = open_connection(ip_address=ip, settings=settings)
        source_files_location = "%s@%s" % (self.boto_settings['platform'], cloud_path)
        source_files_url = smartconnector.get_url_with_pkey(self.boto_settings, source_files_location,
            is_relative_path=True, ip_address=ip)
        logger.debug('source_files_url=%s' % source_files_url)

        dest_files_url = smartconnector.get_url_with_pkey(
            self.boto_settings, os.path.join(
                self.job_dir, self.output_dir, process_id),
            is_relative_path=False)
        logger.debug('dest_files_url=%s' % dest_files_url)
        #hrmcstages.delete_files(dest_files_url, exceptions=[]) #FIXme: uncomment as needed
        # FIXME: might want to turn on paramiko compress function
        # to speed up this transfer
        hrmcstages.copy_directories(source_files_url, dest_files_url)


    def process(self, run_settings):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """

        self.contextid = run_settings['http://rmit.edu.au/schemas/system'][u'contextid']

        #TODO: we assume relative path BDP_URL here, but could be made to work with non-relative (ie., remote paths)
        self.job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']

        try:
            self.finished_nodes = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/stages/run/finished_nodes')
        except KeyError:
            self.finished_nodes = '[]'

        try:
            self.id = int(smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/system/misc/id'))
            self.output_dir = "output_%s" % self.id
        except KeyError, e:
            self.id = 0
            self.output_dir = "output"

        logger.debug("output_dir=%s" % self.output_dir)
        logger.debug("run_settings=%s" % run_settings)
        logger.debug("Wait stage process began")

        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        retrieve_boto_settings(run_settings, self.boto_settings)

        logger.debug("boto_settings=%s" % self.boto_settings)
        #self.nodes = botocloudconnector.get_rego_nodes(self.boto_settings)
        processes = self.executed_procs
        self.error_nodes = []
        # TODO: parse finished_nodes input
        logger.debug('self.finished_nodes=%s' % self.finished_nodes)
        self.finished_nodes = ast.literal_eval(self.finished_nodes)

        for process in processes:
            #instance_id = node.id
            ip_address = process['ip_address']
            process_id = process['id']
            #ip = botocloudconnector.get_instance_ip(instance_id, self.boto_settings)
            #ssh = open_connection(ip_address=ip, settings=self.boto_settings)
            #if not botocloudconnector.is_instance_running(node):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                #FIXME: should error nodes be counted as finished?
            #    logging.error('Instance %s not running' % instance_id)
            #    self.error_nodes.append(node)
            #    continue
            fin = self.job_finished(ip_address, process_id, self.boto_settings)
            logger.debug("fin=%s" % fin)
            if fin:
                print "done. output is available"

                logger.debug("node=%s" % str(process))
                logger.debug("finished_nodes=%s" % self.finished_nodes)
                #FIXME: for multiple nodes, if one finishes before the other then
                #its output will be retrieved, but it may again when the other node fails, because
                #we cannot tell whether we have prevous retrieved this output before and finished_nodes
                # is not maintained between triggerings...

                if not (int(process_id) in [int(x['id']) for x in self.finished_nodes]):
                    self.get_output(ip_address, process_id, self.output_dir, self.boto_settings)

                    audit_url = smartconnector.get_url_with_pkey(
                        self.boto_settings, os.path.join(
                            self.output_dir, process_id, "audit.txt"),
                        is_relative_path=True)

                    fsys = hrmcstages.get_filesystem(audit_url)
                    logger.debug("Audit file url %s" % audit_url)
                    if fsys.exists(audit_url):
                        fsys.delete(audit_url)
                    self.finished_nodes.append(process)
                    logger.debug('finished_processes=%s' % self.finished_nodes)
                    for iterator, p in enumerate(self.all_processes):
                        if int(p['id']) == int(process_id):
                            self.all_processes[iterator]['status'] = 'completed'
                    for iterator, p in enumerate(self.executed_procs):
                        if int(p['id']) == int(process_id):
                            self.executed_procs[iterator]['status'] = 'completed'
                    for iterator, p in enumerate(self.current_processes):
                        if int(p['id']) == int(process_id):
                            self.current_processes[iterator]['status'] = 'completed'

                else:
                    logger.info("We have already "
                        + "processed output of %s on node %s" % (process_id, ip_address))
            else:
                print "job %s still running on %s" % (process_id, ip_address)


    def output(self, run_settings):
        """
        Output new runs_left value (including zero value)
        """
        logger.debug("finished stage output")
        nodes_working = len(self.executed_procs) - len(self.finished_nodes)
        logger.debug("self.executed_procs=%s" % self.executed_procs)
        logger.debug("self.finished_nodes=%s" % self.finished_nodes)

        #FIXME: nodes_working can be negative

        # FIXME: possible race condition?
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
            run_settings['http://rmit.edu.au/schemas/stages/run'] = {}
        #run_settings['http://rmit.edu.au/schemas/stages/run']['runs_left'] = nodes_working
        #run_settings['http://rmit.edu.au/schemas/stages/run']['error_nodes'] = nodes_working

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/run',
            {})[u'runs_left'] = nodes_working

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/run',
            {})[u'error_nodes'] = nodes_working


        if not nodes_working:
            self.finished_nodes = []
        #run_settings['http://rmit.edu.au/schemas/stages/run']['finished_nodes'] = str(self.finished_nodes)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/run',
            {})[u'finished_nodes'] = str(self.finished_nodes)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'all_processes'] = str(self.all_processes)
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'current_processes'] = str(self.current_processes)

        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/execute',
            {})[u'executed_procs'] = str(self.executed_procs)
        return run_settings


def retrieve_boto_settings(run_settings, boto_settings):
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/setup/payload_destination')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/system/platform')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/nectar_username')
    smartconnector.copy_settings(boto_settings, run_settings,
        'http://rmit.edu.au/schemas/stages/create/nectar_password')
    boto_settings['username'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
    boto_settings['username'] = 'root'  # FIXME: schema value is ignored
    boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']
    key_file = hrmcstages.retrieve_private_key(boto_settings,
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nectar_private_key'])
    boto_settings['private_key'] = key_file
    boto_settings['nectar_private_key'] = key_file

