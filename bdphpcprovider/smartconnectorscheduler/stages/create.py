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

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.reliabilityframework.failuredetection import FailureDetection
from bdphpcprovider.reliabilityframework.failurerecovery import FailureRecovery


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

class Create(Stage):

    def __init__(self, user_settings=None):
        self.group_id = ''
        self.platform = None

    def triggered(self, run_settings):
        """
            Return True if there is a platform
            but not group_id
        """
        if self._exists(run_settings,
            RMIT_SCHEMA + '/stages/configure',
            'configure_done'):
                configure_done = run_settings[RMIT_SCHEMA + '/stages/configure'][u'configure_done']
                if configure_done:
                    if not self._exists(run_settings,
                        RMIT_SCHEMA + '/stages/create', 'group_id'):
                        if self._exists(run_settings,
                            RMIT_SCHEMA + '/system', 'platform'):
                            self.platform = run_settings[RMIT_SCHEMA + '/system'][u'platform']
                            return True
        return False

    def process(self, run_settings):
        """
        Make new VMS and store group_id
        """
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        number_vm_instances = run_settings[RMIT_SCHEMA + '/input/system/cloud'][u'number_vm_instances']
        min_number_vms = run_settings[RMIT_SCHEMA + '/input/system/cloud'][u'minimum_number_vm_instances']
        logger.debug("VM instance %d" % number_vm_instances)

#http://rmit.edu.au/schemas/platform/computation


        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/vm_image')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/platform/computation/vm_image_size')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA + '/stages/create/security_group')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/group_id_dir')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/custom_prompt')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/stages/create/cloud_sleep_interval')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA + '/platform/computation/username')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA + '/platform/computation/password')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA + '/platform/computation/private_key')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/platform/computation/security_group')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/platform/computation/ec2_access_key')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/platform/computation/ec2_secret_key')

        bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
        #fixme: in the schema definition, change private_key to private_key_name, private_key_path to private_key
        private_key_relative = run_settings[RMIT_SCHEMA + '/platform/computation']['private_key_path']
        logger.debug('private_key_relative=%s' % private_key_relative)

        local_settings['private_key'] = os.path.join(bdp_root_path, private_key_relative)

        logger.debug('private_key=%s' % local_settings['private_key'])
        local_settings['private_key_name'] = run_settings[RMIT_SCHEMA + '/platform/computation']['private_key']

        logger.debug(run_settings[RMIT_SCHEMA + '/platform/computation']['security_group'])
        #local_settings['username'] = run_settings[
        #    RMIT_SCHEMA + '/platform/computation']['username']
        #local_settings['password'] = run_settings[
        #    RMIT_SCHEMA + '/platform/computation']['password']
        local_settings['username'] = 'root'  # FIXME: schema value is ignored

        #key_file = hrmcstages.retrieve_private_key(local_settings,
        #    run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nectar_private_key'])

        key_file = os.path.join(bdp_root_path, private_key_relative)
        #local_settings['private_key'] = run_settings[RMIT_SCHEMA + '/platform/computation']['private_key']
        #local_settings['nectar_private_key'] = key_file

        logger.debug("botosettings=%s" % local_settings)
        #self.group_id = create_environ(number_vm_instances, local_settings)
        self.nodes = botocloudconnector.create_environ(
            number_vm_instances,
            local_settings)
        logger.debug('node initialisation done')
        logger.debug("self.nodes=%s" % self.nodes)
        logger.debug("len(self.nodes)=%s" % len(self.nodes))
        logger.debug("min_number_vms=%s" % min_number_vms)
        #check if sufficient no. node created
        failure_detection = FailureDetection()
        failure_recovery = FailureRecovery()
        #fixme add no retries
        if not failure_detection.sufficient_vms(len(self.nodes), min_number_vms):
            if not failure_recovery.recovered_insufficient_vms_failure():
                self.group_id = 'UNKNOWN'  # FIXME: do we we mean '' or None here?
                smartconnector.error(run_settings, "error: sufficient VMS cannot be created")
                logger.info("Sufficient number VMs cannot be created for this computation."
                            "Increase your quota or decrease your minimum requirement")
                return

        if self.nodes:
            self.nodes = botocloudconnector.get_ssh_ready_instances(
                self.nodes, local_settings)

        if self.nodes:
            self.group_id, self.nodes = botocloudconnector.brand_instances(
                self.nodes, local_settings)

        botocloudconnector.print_all_information(local_settings,
                                                 all_instances=self.nodes)
        smartconnector.info(run_settings, "1: create (% nodes created" % len(self.nodes))

        #Fixme: the following should transfer power to FT managers
        if not self.group_id:
            self.group_id = 'UNKNOWN'  # FIXME: do we we mean '' or None here?
            logger.debug("No new VM instance can be created for this computation. Retry later.")
            #clear_temp_files(run_settings)

    def output(self, run_settings):
        """
        Inserting a new group if into run settings.
        """
        run_settings.setdefault(
            RMIT_SCHEMA + '/stages/create', {})[u'group_id'] \
            = self.group_id

        if not self.nodes:
            run_settings.setdefault(
            RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] = []
        else:
            if self.group_id is "UNKNOWN":
                run_settings.setdefault(
                    RMIT_SCHEMA + '/reliability', {})[u'cleanup_nodes'] \
                    = [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes]
            else:
                run_settings.setdefault(
                    RMIT_SCHEMA + '/stages/create', {})[u'created_nodes'] \
                    = [(x.id, x.ip_address, unicode(x.region)) for x in self.nodes]
        logger.debug("Updated run settings %s" % run_settings)
        return run_settings
