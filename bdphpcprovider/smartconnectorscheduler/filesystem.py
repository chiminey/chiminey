# Copyright (C) 2012, RMIT University

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


import os
import os.path
import time
import re

from fs.osfs import OSFS
from fs import path
from fs.errors import ResourceNotFoundError
from fs.path import join
import shutil
import tempfile

import logging
import logging.config


#from bdphpcprovider.smartconnectorscheduler.hrmcimpl import get_output
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import get_instance_ip
from bdphpcprovider.smartconnectorscheduler.sshconnector import put_file, open_connection, find_remote_files, get_file


logger = logging.getLogger(__name__)

#TODO: make filesystem-specific exceptions


class FileSystem(object):
    # FIXME: these methods should not interact with the underlying filesystem
    # directory, and should only interact vis osfs api calls.  For example,
    # use fs.mkdir not os.mkdir.
    # FIXME: remove os.path.join references and use fs.path.join instead
    # TODO: replace this with a File based abstraction such as django.storages.backend.

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

    def get_global_filesystem(self):
        return self.global_filesystem

    def create_local_filesystem(self, local_filesystem):
        """
        Creates an additional local filesystem in
        addition to those created at init
        """
        #FIXME: should throw exception if already exists
        if not self.connector_fs.exists(local_filesystem):
            self.connector_fs.makedir(local_filesystem)
        return True

    def create(self, local_filesystem, data_object, message='CREATED'):
        if not self.connector_fs.exists(local_filesystem):
            logger.error("Destination filesystem '%s' does not exist"
                         % local_filesystem)
            raise IOError("Destination filesystem '%s' does not exist"
                          % local_filesystem)

        destination_file_name = os.path.join(self.global_filesystem,
                                             local_filesystem,
                                             data_object.getName())
        if not local_filesystem:
            destination_file_name = os.path.join(self.global_filesystem,
                                                 data_object.getName())

        destination_file = open(destination_file_name, 'w')
        destination_file.write(data_object.getContent())
        destination_file.close()
        logger.info("File '%s' %s" % (destination_file_name, message))
        return True

    def create_under_dir(self, local_filesystem, directory,
                         data_object, message='CREATED'):
        if not self.connector_fs.exists(local_filesystem):
            logger.debug("error")
            logger.error("Destination filesystem '%s' does not exist"
                         % local_filesystem)
            return False
        #mport ipdb
        #ipdb.set_trace()
        direct = path.join("/", local_filesystem, directory)
        logger.debug("direct = %s" % direct)
        self.connector_fs.makedir(direct, allow_recreate=True)
        dest_file_name = path.join(direct, data_object.getName())
        logger.debug("dest_file_name = %s" % dest_file_name)
        #FIXME: Not sure why we need this
        #if not local_filesystem:
        #    destination_file_name = os.path.join(self.global_filesystem,
        #                                        data_object.getName())
        dest_file = self.connector_fs.open(dest_file_name, 'w')
        dest_file.write(data_object.getContent())
        dest_file.close()
        logger.debug("FileX '%s' %s" % (dest_file, message))
        return True

    def retrieve_new(self, directory, file):
        """
        Return the Dataobject for the file in the directory
        Throws IOError if not found
        """
        # This has the advantage of not exposing the path join semantics.
        return self.retrieve(path.join(directory, file))

    def retrieve_under_dir(self, local_filesystem, directory, file):
        # This has the advantage of not exposing the path join semantics.
        return self.retrieve(path.join(local_filesystem,
                                       directory, file))

    def retrieve(self, file_to_be_retrieved):
        # NOTE: Deprecated, as requires full path
        #       to created externally, which is
        # leaky abstraction
        if not self.connector_fs.exists(file_to_be_retrieved):
            logger.error("File'%s' does not exist" % file_to_be_retrieved)
            raise IOError("File'%s' does not exist" % file_to_be_retrieved)

        retrieved_file_absolute_path = os.path.join(self.global_filesystem,
                                                    file_to_be_retrieved)
        retrieved_file = open(retrieved_file_absolute_path, 'r')
        retrieved_file_content = retrieved_file.read()
        retrieved_file_name = os.path.basename(file_to_be_retrieved)
        retrieved_file.close()

        data_object = DataObject(retrieved_file_name)
        data_object.setContent(retrieved_file_content)
        return data_object

    def update(self, local_filesystem, data_object):
        file_to_be_updated = os.path.join(local_filesystem,
                                          data_object.getName())
        if not self.connector_fs.exists(file_to_be_updated):
            logger.error("File'%s' does not exist" % file_to_be_updated)
            raise IOError("File'%s' does not exist" % file_to_be_updated)
       #logger.info("Updating file '%s'" % file_to_be_updated)
        return self.create(local_filesystem, data_object, message="UPDATED")

    def delete(self, file_to_be_deleted):
        # file to be deleted is path not file
        if not self.connector_fs.exists(file_to_be_deleted):
            logger.error("File'%s' does not exist" % file_to_be_deleted)
            raise IOError("File'%s' does not exist" % file_to_be_deleted)

        self.connector_fs.remove(file_to_be_deleted)
        logger.info("File '%s' DELETED" % file_to_be_deleted)
        return True

    def isdir(self, local_filesystem, dir_path):
        joined_path = path.join("/", local_filesystem, dir_path)
        return self.connector_fs.isdir(joined_path)

    def isfile(self, local_filesystem, dir_path, f):
        joined_path = path.join("/", local_filesystem, dir_path, f)
        return self.connector_fs.isfile(joined_path)

    def exists(self, local_filesystem, dir_path, f):
        joined_path = path.join("/", local_filesystem, dir_path, f)
        return self.connector_fs.exists(joined_path)

    def get_local_subdirectories(self, local_filesystem):
        """
        Returns list of names of directories immediately below local_filesystem
        """
        path_to_subdirectories = os.path.join(self.global_filesystem,
                                              local_filesystem)

        logger.debug("Gloabl FS %s Path to Subdir %s" %(self.global_filesystem,
                                                        path_to_subdirectories))
        list_of_subdirectories = os.listdir(path_to_subdirectories)

        logger.debug("List of Directories %s" % list_of_subdirectories)

        return list_of_subdirectories

    def get_local_subdirectory_files(self, local_filesystem, directory):
        """
        Returns list of names of directories immediately below local_filesystem
        """
        path_to_subdirectories = os.path.join(self.global_filesystem,
                                              local_filesystem, directory)
        list_of_subdirectories = os.listdir(path_to_subdirectories)

        return list_of_subdirectories

    def delete_local_filesystem(self, local_filesystem):
        """
        Deleted a local file system
        """
        path_to_local_filesystem = path.join(self.global_filesystem,
                                             local_filesystem)
        #FIXME: should use appropriate osfs API here
        shutil.rmtree(path_to_local_filesystem)

    def local_filesystem_exists(self, local_filesystem):
        return self.connector_fs.exists(path.join("/", local_filesystem))

    def upload_input(self, ssh, local_filesystem, dest):
        input_dir = os.path.join(self.global_filesystem, local_filesystem)
        logger.debug("input_dir =%s" % input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:

            logger.debug("fname=%s" % fname)
            #dest = os.path.join("/home/centos",dest)
            logger.debug("Destination %s" % dest)

            put_file(ssh, input_dir,  fname, dest)

    def upload_iter_input_dir(self, ssh, local_filesystem, iter_inputdir, dest):
        input_dir = os.path.join(self.global_filesystem, local_filesystem, iter_inputdir)
        logger.debug("input_dir =%s" % input_dir)
        dirList = os.listdir(input_dir)
        for fname in dirList:

            logger.debug("fname=%s" % fname)
            #dest = os.path.join("/home/centos",dest)
            logger.debug("Destination %s" % dest)


            put_file(ssh, input_dir,  fname, dest)


    def download_output(self, ssh, instance_id, local_filesystem, settings):
        output_dir = os.path.join(self.global_filesystem,
                                  local_filesystem,
                                  instance_id)
        from bdphpcprovider.smartconnectorscheduler import hrmcimpl
        hrmcimpl.get_output(instance_id, output_dir, settings)





    def exec_command(self, file_to_be_executed, command, wildcard=False):
        import subprocess

        absolute_path_to_file = os.path.join(self.global_filesystem,
                                             file_to_be_executed)
        if wildcard:
            import glob  # FIXME: Why is this here?

        command.append(absolute_path_to_file)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = proc.stdout.read()
        return output

    def copy(self, local_filesystem, source_dir,
             file, dest_dir, new_name, overwrite=True):
        """
        Copy lfs/sourcedir/file to lfs/dest_dir
        """
        try:
            self.connector_fs.copy(path.join(local_filesystem,
                                             source_dir, file),
                                   path.join(dest_dir, new_name),
                                   overwrite)
        except ResourceNotFoundError as e:
            raise IOError(e)  # FIXME: make filesystem specfic exceptions

    def glob(self, local_filesystem, directory, pattern):
        """
        Return list of files in the local_filesystem/directory
        with names that match pattern
        """
        files = self.get_local_subdirectory_files(
            local_filesystem,
            directory)
        logger.debug("files=%s " % files)
        pat = re.compile(pattern)
        new_files = [x for x in files if pat.match(x)]
        return new_files


class DataObject(object):
    # Assume that whole file is contained in one big string
    # as it makes json parsing easier
    # FIXME: There is very little value-add here.
    #        Might be better to just use strings

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
        if '/' in name:
            raise ValueError("Data objects cannot have paths")
        self._name = name

    def setContent(self, content):
        self._content = content

    # TODO: make getters and setters that handle
    #       arrays and serialise/deserialise as JSON

    def __str__(self):
        return '%s = %s' % (self._name, self._content)
