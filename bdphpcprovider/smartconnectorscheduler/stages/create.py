from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler.filesystem import DataObject
from bdphpcprovider.smartconnectorscheduler.hrmcstages import clear_temp_files, \
    get_filesys, get_settings, get_run_info
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ

import json
import sys
import logging

logger = logging.getLogger(__name__)


class Create(Stage):

    def __init__(self, user_settings=None):
        self.user_settings = user_settings
        self.settings = dict(self.user_settings)
        self.group_id = ''
        self.platform = None

    def triggered(self, run_settings):
        """
            Return True if there is a platform
            but not group_id
        """
        #self.settings = get_settings(run_settings)
        #self.run_info = get_run_info(run_settings)

        logger.debug("User_settings %s \n Run_settings %s" % (self.user_settings, run_settings))
        if (not run_settings[u'group_id']) and run_settings[u'flag'] == 0 :
            if u'platform' in run_settings:
                self.platform = run_settings[u'platform']
            self.settings.update(run_settings)
            logger.debug("Settings: %s" % self.settings)
            logger.debug("Create Stage: Triggered")
            run_settings[u'flag'] = 1
            return True
        logger.debug("Create Stage: Not Triggered")
        return False

    def process(self, run_settings):
        """
        Make new VMS and store group_id
        """
        self.settings.update(run_settings)
        number_vm_instances = self.settings[u'number_vm_instances']
        logger.debug("VM instance %d" % number_vm_instances)
        self.group_id = create_environ(number_vm_instances, self.settings)
        if not self.group_id:
            self.group_id = ''
            logger.debug("No new VM instance can be created for this computation. Retry later.")
            #clear_temp_files(run_settings)
            #sys.exit()

    def output(self, run_settings):
        """
        Inserting a new group if into run settings.
        """

        run_settings[u'group_id'] = self.group_id
        logger.debug("Updated run settings %s" % run_settings)
        return run_settings

