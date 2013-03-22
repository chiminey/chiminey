from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection
from bdphpcprovider.smartconnectorscheduler.sshconnector import run_sudo_command
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientResourceError
from bdphpcprovider.smartconnectorscheduler.stages.errors import MissingConfigurationError
from bdphpcprovider.smartconnectorscheduler import hrmcstages
import logging
import os

logger = logging.getLogger(__name__)


class Setup(Stage):
    """
    Handles creation of a running executable on the VMS in a group
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        #self.settings = dict(self.user_settings)
        self.group_id = ''
        self.platform = None
        # We want to isolate all the botoconnector methods from run_settings structure, so
        # build dict to hold user_settings plus needed values.
        self.boto_settings = user_settings.copy()

    def triggered(self, run_settings):
        """
        Triggered if appropriate vms exist and we have not finished setup
        """
        # triggered if the set of the VMS has been established.
        #self.settings = get_all_settings(context)
        #logger.debug("settings = %s" % self.settings)

        # self.settings.update(run_settings)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/create', u'group_id'):
            self.group_id = self.settings['http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False


        logger.debug("group_id = %s" % self.group_id)

        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/setup', u'setup_finished'):
            logger.debug(self.settings['http://rmit.edu.au/schemas/stages/setup'][u'setup_finished'])
            return False

        self.packaged_nodes = botocloudconnector.get_rego_nodes(self.group_id,
            self.boto_settings)
        logger.debug("packaged_nodes = %s" % self.packaged_nodes)

        logger.debug("Setup on %s" % self.settings['http://rmit.edu.au/shemas/system']['platform'])
        return len(self.packaged_nodes)

    def _copy_settings(self, dest_context, context, key):
        dest_context[key] = context[os.path.dirname(key)][os.path.basename(key)]

    def process(self, run_settings):
        """
        Setup all the nodes
        """
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/setup/PAYLOAD_SOURCE')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/setup/PAYLOAD_DESTINATION')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/setup/PAYLOAD_SOURCE')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/VM_IMAGE')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/VM_SIZE')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/SECURITY_GROUP')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/GROUP_ID_DIR')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/CUSTOM_PROMPT')
        self._copy_settings(self.boto_settings, self.run_settings,
            'http://rmit.edu.au/schemas/stages/create/CLOUD_SLEEP_INTERVAL')

        self.setup(self.boto_settings, self.group_id)

    def output(self, run_settings):
        """
        Store number of packages nodes as setup_finished in runinfo.sys
        """
        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/setup'):
            run_settings['http://rmit.edu.au/schemas/stages/setup'] = {}

        run_settings['http://rmit.edu.au/schemas/stages/setup']['setup_finished'] = len(self.packaged_nodes)

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/system/misc'):
            run_settings['http://rmit.edu.au/schemas/system/misc'] = {}

        run_settings['http://rmit.edu.au/schemas/sysystem/misc']['id'] = 0
        #update_key('setup_finished', len(self.packaged_nodes), context)
        # So initial input goes in input_0 directory

        # FIXME: probably should be set at beginning of run or connector?
        #update_key('id', 0, context)

        return run_settings

    def setup(self, settings, group_id, maketarget_nodegroup_pair={}):
        available_nodes = list(botocloudconnector.get_rego_nodes(group_id, settings))
        requested_nodes = 0

        if 'PAYLOAD_SOURCE' not in settings:
            message = "PAYLOAD_SOURCE is not set"
            logger.exception(message)
            raise MissingConfigurationError(message)

        if 'PAYLOAD_DESTINATION' not in settings:
            message = "PAYLOAD_DESTINATION is not set"
            logger.exception(message)
            raise MissingConfigurationError(message)

        if not maketarget_nodegroup_pair:
            EMPTY_MAKE_TARGET = ''
            requested_nodes = len(available_nodes)
            maketarget_nodegroup_pair[EMPTY_MAKE_TARGET] = requested_nodes
        else:
            for i in maketarget_nodegroup_pair.keys():
                requested_nodes += maketarget_nodegroup_pair[i]
            if requested_nodes > len(available_nodes):
                message = "Requested nodes %d; but available nodes %s " \
                    % (requested_nodes, len(available_nodes))
                logger.exception(message)
                raise InsufficientResourceError(message)
        logger.info("Requested nodes %d: \nAvailable nodes %s "
               % (requested_nodes, len(available_nodes)))

        def setup_worker(node_ip, make_target, source, destination):
            logger.info("Setting up node with IP %s using makefile %s" \
                % (node_ip, make_target))
            self.setup_task(settings, node_ip, make_target, source, destination)
            logger.info("Setting up machine with IP %s completed" % node_ip)

        import threading
        threads_running = []
        for make_target in maketarget_nodegroup_pair:
            for i in range(0, maketarget_nodegroup_pair[make_target]):
                logger.debug("starting thread")
                instance = available_nodes[0]
                node_ip = botocloudconnector.get_instance_ip(instance.id, settings)
                source = Stage.get_url_with_pkey(settings, settings['PAYLOAD_SOURCE'])
                destination = Stage.get_url_with_pkey(settings, settings['PAYLOAD_DESTINATION'],
                                                     is_relative_path=True, ip_address=node_ip)
                logger.debug("Source %s" % source)
                logger.debug("Destination %s" % destination)
                t = threading.Thread(target=setup_worker,
                    args=(node_ip, make_target, source, destination))
                threads_running.append(t)
                t.start()
                available_nodes.pop(0)

        for thread in threads_running:
            logger.debug("waiting on thread")
            t.join()
        logger.debug("all threads are done")

    def setup_task(self, settings, node_ip, make_target, source, destination):
        """
        Transfer the task package to the node and install
        """
        hrmcstages.copy_directories(source, destination)

        makefile_path = self.get_make_path(destination)
        # Check whether make is installed. If not install
        check_make_installation = '`command -v make  > /dev/null 2>&1 || echo sudo yum install -y make`; '
        execute_setup = "cd %s; make %s " % (makefile_path, make_target)
        command = check_make_installation + execute_setup
        logger.debug("Setting up environment using makefile with target %s" % make_target)
        logger.info("Setup node with IP %s" % node_ip)
        ssh = open_connection(ip_address=node_ip, settings=settings)
        run_sudo_command(ssh, command, settings, "")

    def get_make_path(self, destination):
        from urlparse import urlparse, parse_qsl
        import os
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
