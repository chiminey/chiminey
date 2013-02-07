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

    def __init__(self):
        self.settings = {}
        self.group_id = ''
        self.provider = None

    def triggered(self, context):
        """
            Return True if there is a file system and a filesystem and there is a provider
            but now group_id
        """
        self.settings = get_settings(context)
        self.run_info = get_run_info(context)

        if self.settings and self.run_info:
            if 'PROVIDER' in self.run_info:
                self.provider = self.run_info['PROVIDER']
                if 'group_id' in self.run_info:
                    return False
                self.settings.update(self.run_info)  # merge all settings

                return True
        return False

    def process(self, context):
        """
        Make new VMS and store group_id
        """
        number_vm_instances = context['number_vm_instances']
        self.seed = context['seed']
        self.group_id = create_environ(number_vm_instances, self.settings)
        if not self.group_id:
            print "No new VM instance can be created for this computation. Retry later."
            clear_temp_files(context)
            sys.exit()

    def output(self, context):
        """
        Create a runfinos.sys file in filesystem with new group_id
        """
        local_filesystem = 'default'
        data_object = DataObject("runinfo.sys")
        data_object.create(json.dumps({'group_id': self.group_id,
                                       'seed': self.seed,
                                       'PROVIDER': self.provider}))
        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)
        return context

