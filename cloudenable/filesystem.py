import os
import time

from fs.osfs import OSFS
import shutil
import tempfile

import logging
import logging.config

from hrmcimpl import _upload_input
from hrmcimpl import get_output


logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class FileSystem(object):
   # def __init__(self, global_filesystem):
        

    def __init__(self, global_filesystem, local_filesystem=None):
        self._create_global_filesystem(global_filesystem)
        if not local_filesystem:
            self._create_global_filesystem(global_filesystem)
            
        elif self.connector_fs.exists(local_filesystem):
            logger.error("Local filesystem '%s' already exists under '%s'"
                         % (local_filesystem, global_filesystem))
        else:
            self.connector_fs.makedir(local_filesystem)
            logger.info("Local filesystem '%s' CREATED under '%s' "
                        % (local_filesystem, global_filesystem))

    def _create_global_filesystem(self, global_filesystem):
        self.global_filesystem = global_filesystem
        self.connector_fs = OSFS(global_filesystem, create=True)
        logger.info("Global filesystem '%s' CREATED " % global_filesystem)

    def create(self, local_filesystem, data_object, message='CREATED'):
        if not self.connector_fs.exists(local_filesystem):
            logger.error("Destination filesystem '%s' does not exist"
                         % local_filesystem)
            return False

        destination_file_name = self.global_filesystem + "/" + local_filesystem + "/" + data_object.getName()
        if not local_filesystem:
            destination_file_name = self.global_filesystem + "/" + data_object.getName()
            
        destination_file = open(destination_file_name, 'w')
        destination_file.write(data_object.getContent())
        destination_file.close()
        logger.info("File '%s' %s" % (destination_file_name, message))
        return True
     # check for missing path# MUST RETURN filesystem
    def retrieve(self, file_to_be_retrieved):
        if not self.connector_fs.exists(file_to_be_retrieved):
            logger.error("File'%s' does not exist" % file_to_be_retrieved)
            return None

        retrieved_file_absolute_path = self.global_filesystem + "/" + file_to_be_retrieved
        retrieved_file = open(retrieved_file_absolute_path, 'r')
        retrieved_file_content = retrieved_file.read()
        retrieved_file_name = os.path.basename(file_to_be_retrieved)
        retrieved_file.close()

        data_object = DataObject(retrieved_file_name)
        data_object.setContent(retrieved_file_content)
        return data_object

    def update(self, local_filesystem, data_object):
        file_to_be_updated = local_filesystem + "/" + data_object.getName()
        if not self.connector_fs.exists(file_to_be_updated):
            logger.error("File'%s' does not exist" % file_to_be_updated)
            return False
       #logger.info("Updating file '%s'" % file_to_be_updated)
        return self.create(local_filesystem, data_object, message="UPDATED")

    def delete(self, file_to_be_deleted):
        if not self.connector_fs.exists(file_to_be_deleted):
            logger.error("File'%s' does not exist" % file_to_be_deleted)
            return False

        self.connector_fs.remove(file_to_be_deleted)
        logger.info("File '%s' DELETED" % file_to_be_deleted)
        return True

    def get_local_subdirectories(self, local_filesystem):
        """
        Returns list of names of directories immediately below local_filesystem
        """
        # TODO
        return []

    def upload_input(self, ssh, local_filesystem, dest):
        input_dir = os.path.join(self.global_filesystem,local_filesystem)
        logger.debug("input_dir =%s" % input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:
            logger.debug("fname=%s" % fname)
            _upload_input(ssh, input_dir,  fname, dest)

    def download_output(self, ssh, instance_id, local_filesystem, settings):
        output_dir = os.path.join(self.global_filesystem, local_filesystem)
        get_output(instance_id, output_dir, settings)


class DataObject(object):
    # Assume that whole file is contained in one big string
    # as it makes json parsing easier

    def __init__(self):
        self._name = ""
        self._content = ""

    def __init__(self, name):
        self._name = name
        self._content = ""

    def create(self, content):
        self._content = content

    def retrieve(self):
        return self._content

    def getName(self):
        return self._name

    def getContent(self):
        return self._content

    def setName(self, name):
        self._name = name

    def setContent(self, content):
        self._content = content

    # TODO: make getters and setters that handle arrays and serialise/deserialise as JSON

    def __str__(self):
        return "%s = %s" % (self._name, self._content)
