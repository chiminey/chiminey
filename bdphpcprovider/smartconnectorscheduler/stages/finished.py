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
import os

from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection
from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcimpl
from bdphpcprovider.smartconnectorscheduler import hrmcstages

logger = logging.getLogger(__name__)


def _status_of_nodeset(fs, nodes, output_dir, settings):
    """
    Return lists that describe which of the set of nodes are finished or
    have disappeared
    """
    error_nodes = []
    finished_nodes = []

    for node in nodes:
        instance_id = node.id
        logger.debug("instance_id = %s" % instance_id)

        if not botocloudconnector.is_instance_running(instance_id, settings):
            # An unlikely situation where the node crashed after is was
            # detected as registered.
            logging.error('Instance %s not running' % instance_id)
            error_nodes.append(node)
            continue

        finished = Finished()
        if finished.job_finished(instance_id, settings):
            print "done. output is available"
            hrmcimpl.get_output(fs, instance_id,
#                       "%s/%s" % (output_dir, instance_id),
                output_dir,
                settings)

            hrmcimpl.run_post_task(instance_id, settings)
            post_output_dir = instance_id + "_post"
            hrmcimpl.get_post_output(instance_id,
                "%s/%s" % (output_dir, post_output_dir),
                settings)

            finished_nodes.append(node)
        else:
            print "job still running on %s: %s\
            " % (instance_id, botocloudconnector.get_instance_ip(instance_id, settings))

    return (error_nodes, finished_nodes)


def packages_complete(fs, group_id, output_dir, settings):
    """
    Indicates if all the package nodes have finished and generate
    any output as needed
    """
    nodes = botocloudconnector.get_rego_nodes(group_id, settings)
    error_nodes, finished_nodes = _status_of_nodeset(fs, nodes,
                                                     output_dir,
                                                     settings)
    if finished_nodes + error_nodes == nodes:
        logger.info("Package Finished")
        return True

    if error_nodes:
        logger.warn("error nodes: %s" % error_nodes)
        return True

    return False


class Finished(Stage):
    """
        Return whether the run has finished or not
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.runs_left = 0
        self.error_nodes = 0
        self.job_dir = "hrmcrun"  # TODO: make a stageparameter + suffix on real job number
        self.boto_settings = user_settings.copy()
        logger.debug("finished stage initialised")

    def triggered(self, run_settings):
        """
            Checks whether there is a non-zero number of runs still going.
        """
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/create', u'group_id'):
            self.group_id = run_settings['http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
        logger.debug("group_id = %s" % self.group_id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc', u'id'):
            self.id = run_settings['http://rmit.edu.au/schemas/system/misc'][u'id']
            self.output_dir = "output_%s" % self.id
        else:
            self.id = 0
            self.output_dir = "output"

        logger.debug("output_dir=%s" % self.output_dir)

        # if 'id' in self.settings:
        #     self.id = self.settings['id']
        #     self.output_dir = "output_%s" % self.id
        # else:
        #     self.output_dir = "output"

        # if we have no runs_left then we must have finished all the runs
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run', u'runs_left'):
            return run_settings['http://rmit.edu.au/schemas/stages/run'][u'runs_left']

        # if 'runs_left' in self.settings:
        #     return self.settings['runs_left']
        return False

    def job_finished(self, instance_id, settings):
        """
            Return True if package job on instance_id has job_finished
        """
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip, settings=settings)
        makefile_path = settings['payload_destination']

        command = "cd %s; make %s" % (makefile_path, 'running')

        #command_out, _ = sshconnector.run_sudo_command(ssh, command, settings, instance_id)
        command_out, _ = sshconnector.run_command_with_status(ssh, command)

        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if 'stillrunning' in line:
                    return False

        return True  # FIXME: this may be undesirable

    def get_output(self, instance_id, output_dir, settings):
        """
            Retrieve the output from the task on the node
        """
        logger.info("get_output %s" % instance_id)

        cloud_path = os.path.join(self.boto_settings['payload_destination'],
                                  self.boto_settings['payload_cloud_dirname'])
        logger.debug("cloud_path=%s" % cloud_path)
        logger.debug("Transferring output from %s to %s" % (cloud_path, output_dir))
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        #ssh = open_connection(ip_address=ip, settings=settings)
        source_files_location = "%s@%s" % (self.boto_settings['platform'], cloud_path)
        source_files_url = smartconnector.get_url_with_pkey(self.boto_settings, source_files_location,
            is_relative_path=True, ip_address=ip)
        logger.debug('source_files_url=%s' % source_files_url)
        dest_files_url = smartconnector.get_url_with_pkey(self.boto_settings,
                                                          os.path.join(self.job_dir, self.output_dir,
                                                                       instance_id), is_relative_path=True)
        logger.debug('dest_files_url=%s' % dest_files_url)
        hrmcstages.delete_files(dest_files_url, exceptions=[])
        hrmcstages.copy_directories(source_files_url, dest_files_url)

    def process(self, run_settings):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """

        logger.debug("Finished stage process began")

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
        self.boto_settings['private_key'] = self.user_settings['nectar_private_key']
        self.boto_settings['username'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['password'] = run_settings['http://rmit.edu.au/schemas/stages/create']['nectar_password']

        self.nodes = botocloudconnector.get_rego_nodes(self.group_id, self.boto_settings)

        self.error_nodes = []
        self.finished_nodes = []
        for node in self.nodes:
            instance_id = node.id
            #ip = botocloudconnector.get_instance_ip(instance_id, self.boto_settings)
            #ssh = open_connection(ip_address=ip, settings=self.boto_settings)
            if not botocloudconnector.is_instance_running(instance_id, self.boto_settings):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                #FIXME: should error nodes be counted as finished?
                logging.error('Instance %s not running' % instance_id)
                self.error_nodes.append(node)
                continue
            fin = self.job_finished(instance_id, self.boto_settings)
            logger.debug("fin=%s" % fin)
            if fin:
                print "done. output is available"

                logger.debug("node=%s" % node)
                logger.debug("finished_nodes=%s" % self.finished_nodes)
                #FIXME: for multiple nodes, if one finishes before the other then
                #its output will be retrieved, but it may again when the other node fails, because
                #we cannot tell whether we have prevous retrieved this output before and finished_nodes
                # is not maintained between triggerings...

                if not (node.id in [x.id for x in self.finished_nodes]):
                    self.get_output(instance_id, self.output_dir, self.boto_settings)

                    audit_url = smartconnector.get_url_with_pkey(self.boto_settings,
                                                          os.path.join(self.output_dir,
                                                                       instance_id, "audit.txt"), is_relative_path=True)

                    fsys = hrmcstages.get_filesystem(audit_url)
                    logger.debug("Audit file url %s" % audit_url)
                    if fsys.exists(audit_url):
                        fsys.delete(audit_url)
                else:
                    logger.info("We have already "
                        + "processed output from node %s" % node.id)
                self.finished_nodes.append(node)
            else:
                print "job still running on %s: %s\
                " % (instance_id,
                     botocloudconnector.get_instance_ip(instance_id, self.boto_settings))

    def output(self, run_settings):
        """
        Output new runs_left value (including zero value)
        """
        logger.debug("finished stage output")
        nodes_working = len(self.nodes) - len(self.finished_nodes)

        # FIXME: possible race condition?
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/run'):
            run_settings['http://rmit.edu.au/schemas/stages/run'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/run']['runs_left'] = nodes_working
        run_settings['http://rmit.edu.au/schemas/stages/run']['error_nodes'] = nodes_working

        #update_key('error_nodes', len(self.error_nodes), context)
        #update_key('runs_left', nodes_working, context)
        # NOTE: runs_left cannot be deleted or run() will trigger
        return run_settings
