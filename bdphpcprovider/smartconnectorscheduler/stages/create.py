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

from bdphpcprovider.cloudconnection import create_vms, print_vms
from bdphpcprovider.platform import manage
from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.reliabilityframework.failuredetection import FailureDetection
from bdphpcprovider.reliabilityframework.failurerecovery import FailureRecovery

from bdphpcprovider.runsettings import (
    getval, setval, SettingNotFoundException, IncompatibleTypeException)


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

        try:
            configure_done = int(getval(run_settings,
                '%s/stages/configure/configure_done' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            return False

        if configure_done:
            try:
                group_id = getval(run_settings,
                       '%s/stages/create/group_id' % RMIT_SCHEMA)
            except SettingNotFoundException:
                try:
                    self.platform_type = getval(run_settings, '%s/system/platform' % RMIT_SCHEMA)
                    return True
                except SettingNotFoundException:
                    pass

        return False

        # if self._exists(run_settings,
        #     RMIT_SCHEMA + '/stages/configure',
        #     'configure_done'):
        #         configure_done = run_settings[
        #             RMIT_SCHEMA + '/stages/configure'][u'configure_done']
        #         if configure_done:
        #             if not self._exists(run_settings,
        #                 RMIT_SCHEMA + '/stages/create', 'group_id'):
        #                 if self._exists(run_settings,
        #                     RMIT_SCHEMA + '/system', 'platform'):
        #                     self.platform_type = run_settings[
        #                         RMIT_SCHEMA + '/system'][u'platform']
        #                     return True
        # return False

    def process(self, run_settings):
        """
        Make new VMS and store group_id
        """
        messages.info(run_settings, "1: create")
        local_settings = {}
        #todo: remove system/platform dependency
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/vm_image')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/group_id_dir')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/custom_prompt')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/cloud_sleep_interval')
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

        number_vm_instances = run_settings[RMIT_SCHEMA + '/input/system/cloud'][u'number_vm_instances']
        min_number_vms = run_settings[RMIT_SCHEMA + '/input/system/cloud'][u'minimum_number_vm_instances']
        logger.debug("VM instance %d" % number_vm_instances)
        self.platform_type = local_settings['platform_type']
        self.group_id, self.nodes = create_vms(
            number_vm_instances,
            local_settings)
        logger.debug('node initialisation done')
        #todo: cleanup nodes with Error state, and also nodes that are spawning indefinitely (timeout)
        #check if sufficient no. node created
        failure_detection = FailureDetection()
        failure_recovery = FailureRecovery()
        #fixme add no retries
        if not failure_detection.sufficient_vms(len(self.nodes), min_number_vms):
            if not failure_recovery.recovered_insufficient_vms_failure():
                self.group_id = 'UNKNOWN'  # FIXME: do we we mean '' or None here?
                messages.error(run_settings, "error: sufficient VMS cannot be created")
                logger.info("Sufficient number VMs cannot be created for this computation."
                            "Increase your quota or decrease your minimum requirement")
                return

        print_vms(local_settings, all_vms=self.nodes)
        messages.info(run_settings, "1: create (%s nodes created)" % len(self.nodes))

        #Fixme: the following should transfer power to FT managers
        if not self.group_id:
            self.group_id = 'UNKNOWN'  # FIXME: do we we mean '' or None here?
            logger.debug("No new VM instance can be created for this computation. Retry later.")
            #clear_temp_files(run_settings)

    def output(self, run_settings):
        """
        Inserting a new group if into run settings.
        """
        logger.debug('output')

        setval(run_settings,
               '%s/stages/create/group_id' % RMIT_SCHEMA,
               self.group_id)
        # run_settings.setdefault(
        #     RMIT_SCHEMA + '/stages/create', {})[u'group_id'] \
        #     = self.group_id

        setval(run_settings,
               '%s/system/platform' % RMIT_SCHEMA,
               self.platform_type)
        # run_settings.setdefault(
        #     RMIT_SCHEMA + '/system', {})[u'platform'] \
        #     = self.platform_type

        if not self.nodes:
            setval(run_settings,
             '%s/stages/create/created_nodes' % RMIT_SCHEMA, [])
            # run_settings.setdefault(
            # RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] = []
        else:
            for node in self.nodes:
                if not node.ip_address:
                    node.ip_address = node.private_ip_address
            if self.group_id is "UNKNOWN":
                setval(run_settings,
                       "%s/reliability/cleanup_nodes" % RMIT_SCHEMA,
                        [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes])
                # run_settings.setdefault(
                #     RMIT_SCHEMA + '/reliability', {})[u'cleanup_nodes'] \
                #     = [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes]
            else:
                setval(run_settings,
                       "%s/stages/create/created_nodes" % RMIT_SCHEMA,
                       [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes])

                # run_settings.setdefault(
                #     RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] \
                #     = [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes]
        logger.debug("Updated run settings %s" % run_settings)
        return run_settings
