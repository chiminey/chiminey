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

import logging

from bdphpcprovider.cloudconnection import create_vms, print_vms
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages import stage
from bdphpcprovider.corestages.stage import Stage
from bdphpcprovider.smartconnectorscheduler.stages.errors import InsufficientVMError
from bdphpcprovider.reliabilityframework import FTManager
from bdphpcprovider import messages

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Create(Stage):
    def __init__(self, user_settings=None):
        self.group_id = ''
        self.platform_type = None
        logger.debug("Create stage initialized")

    def triggered(self, run_settings):
        """
            Return True if there is a platform
            but not group_id
        """
        if self._exists(run_settings,
            RMIT_SCHEMA + '/stages/configure',
            'configure_done'):
                configure_done = run_settings[
                    RMIT_SCHEMA + '/stages/configure'][u'configure_done']
                if configure_done:
                    if not self._exists(run_settings,
                        RMIT_SCHEMA + '/stages/create', 'group_id'):
                        if self._exists(run_settings,
                            RMIT_SCHEMA + '/system', 'platform'):
                            self.platform_type = run_settings[
                                RMIT_SCHEMA + '/system'][u'platform']
                            return True
        return False

    def process(self, run_settings):
        """
        Make new VMS and store group_id
        """
        messages.info(run_settings, "1: create")
        local_settings = {}
        #todo: remove system/platform dependency
        stage.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/platform')
        stage.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/vm_image')
        stage.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/group_id_dir')
        stage.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/custom_prompt')
        stage.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/cloud_sleep_interval')
        local_settings['min_count'] = run_settings[RMIT_SCHEMA + '/input/system/cloud']['minimum_number_vm_instances']
        local_settings['max_count'] = run_settings[RMIT_SCHEMA + '/input/system/cloud']['number_vm_instances']
        logger.debug('local_settings=%s' % local_settings)

        computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        try:
            comp_pltf_settings = manage.get_platform_settings(computation_platform_url, bdp_username)
        except KeyError:
            #Fixme: the following should transfer power to FT managers
            self.group_id = 'UNKNOWN'
            self.nodes = []
            return
        local_settings.update(comp_pltf_settings)
        logger.debug('local_settings=%s' % local_settings)
        self.platform_type = local_settings['platform_type']
        self.group_id, self.nodes = create_vms(local_settings)
        try:
            if not self.nodes or len(self.nodes) < local_settings['min_count']:
                raise InsufficientVMError
            print_vms(local_settings, all_vms=self.nodes)
            messages.info(run_settings, "1: create (%s nodes created)" % len(self.nodes))
        except InsufficientVMError as e:
            self.group_id = 'UNKNOWN'
            messages.error(run_settings, "error: sufficient VMs cannot be created")
            ftmanager = FTManager()
            ftmanager.manage_failure(e, settings=comp_pltf_settings,
                                     created_vms=self.nodes)


    def output(self, run_settings):
        """
        Inserting a new group if into run settings.
        """
        logger.debug('output')
        run_settings.setdefault(
            RMIT_SCHEMA + '/stages/create', {})[u'group_id'] \
            = self.group_id
        run_settings.setdefault(
            RMIT_SCHEMA + '/system', {})[u'platform'] \
            = self.platform_type
        if not self.nodes:
            run_settings.setdefault(
            RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] = []
        else:
            for node in self.nodes:
                if not node.ip_address:
                    node.ip_address = node.private_ip_address
            if self.group_id is not  "UNKNOWN":
                run_settings.setdefault(
                    RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] \
                    = [[x.id, x.ip_address, unicode(x.region), 'running'] for x in self.nodes]
        logger.debug("Updated run settings %s" % run_settings)
        return run_settings
