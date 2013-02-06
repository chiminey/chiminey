
import logging

from bdphpcprovider.smartconnectorscheduler.sshconnector import get_package_pids, open_connection

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI, SmartConnector

from bdphpcprovider.smartconnectorscheduler import botocloudconnector

from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_settings, \
    get_run_info, get_filesys, get_file, get_run_settings, update_key


logger = logging.getLogger(__name__)


class Finished(Stage):
    """
        Return whether the run has finished or not
    """

    def __init__(self):
        self.runs_left = 0
        self.error_nodes = 0

    def triggered(self, context):
        """
            Checks whether there is a non-zero number of runs still going.
        """
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings['group_id']
        logger.debug("group_id = %s" % self.group_id)

        if 'id' in self.settings:
            self.id = self.settings['id']
            self.output_dir = "output_%s" % self.id
        else:
            self.output_dir = "output"

        # if we have no runs_left then we must have finished all the runs
        if 'runs_left' in self.settings:
            return self.settings['runs_left']
        logger.debug("Finished NOT Triggered")
        return False

    def job_finished(self, instance_id, settings):
        """
            Return True if package job on instance_id has job_finished
        """
        ip = botocloudconnector.get_instance_ip(instance_id, settings)
        ssh = open_connection(ip_address=ip, settings=settings)
        pids = get_package_pids(ssh, settings['COMPILE_FILE'])
        logger.debug("pids=%s" % repr(pids))
        return pids == [""]

    def process(self, context):
        """
            Check all registered nodes to find whether
            they are running, stopped or in error_nodes
        """
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)

        logger.debug("Finished stage process began")
        self.nodes = botocloudconnector.get_rego_nodes(self.group_id, self.settings)

        self.error_nodes = []
        self.finished_nodes = []
        for node in self.nodes:
            instance_id = node.id
            ip = botocloudconnector.get_instance_ip(instance_id, self.settings)
            ssh = open_connection(ip_address=ip, settings=self.settings)
            if not botocloudconnector.is_instance_running(instance_id, self.settings):
                # An unlikely situation where the node crashed after is was
                # detected as registered.
                #FIXME: should error nodes be counted as finished?
                logging.error('Instance %s not running' % instance_id)
                self.error_nodes.append(node)
                continue
            fin = self.job_finished(instance_id, self.settings)
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
                    fsys.download_output(ssh, instance_id, self.output_dir, self.settings)
                    import os
                    audit_file = os.path.join(self.output_dir, instance_id, "audit.txt")
                    logger.debug("Audit file path %s" % audit_file)
                    if  fsys.exists(self.output_dir, instance_id, "audit.txt"):
                        fsys.delete(audit_file)
                else:
                    logger.info("We have already "
                        + "processed output from node %s" % node.id)
                self.finished_nodes.append(node)
            else:
                print "job still running on %s: %s\
                " % (instance_id,
                     botocloudconnector.get_instance_ip(instance_id, self.settings))

    def output(self, context):
        """
        Output new runs_left value (including zero value)
        """
        nodes_working = len(self.nodes) - len(self.finished_nodes)
        update_key('runs_left', nodes_working, context)
        # FIXME: possible race condition?
        update_key('error_nodes', len(self.error_nodes), context)
        update_key('runs_left', nodes_working, context)

        # NOTE: runs_left cannot be deleted or run() will trigger
        return context