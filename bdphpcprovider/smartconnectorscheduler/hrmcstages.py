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

# Contains the specific connectors and stages for HRMC

import sys
import os
import time
import logging
import logging.config
import json
import os
import sys
import re

logger = logging.getLogger(__name__)

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI, SmartConnector
from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, \
    collect_instances, destroy_environ
from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler import models

from django.core.files.storage import FileSystemStorage



def get_filesys(context):
    """
    Return the filesys in the context
    """
    try:
        val = context['filesys']
    except KeyError:
        message = 'Context missing "filesys" key'
        logger.exception(message)
        raise ContextKeyMissing(message)
    return val


def _load_file(fsys, fname):
    """
    Returns the dataobject for fname in fsys, or empty data object if error
    """
    try:
        config = fsys.retrieve(fname)
    except KeyError, e:
        config = DataObject(fname, '')
        logger.warn("Cannot load %s %s" % (fname, e))
    return config


def retrieve_settings(context):
    """
    Using the user_id in the context, retrieves all the settings files from the profile models
    """
    user_id = context['user_id']
    user = models.User.objects.get(id=user_id)
    profile = user.get_profile()
    settings = {}
    for param in models.UserProfileParameter.objects.filter(paramset__user_profile=profile):

        try:
            settings[param.name.name] = param.getValue()
        except Exception:
            logger.error("Invalid settings values found for %s"% param)
            raise BadInputException()
        logger.debug("%s %s %s" % (param.paramset.schema, param.name,
            param.getValue()))

    return settings


def get_file_from_context(context, fname):
    """
    Retrieve the content of a remote file with fname
    """
    fsys_path = context['fsys']
    remote_fs = FileSystemStorage(location=fsys_path)
    f = context[fname]
    content = remote_fs.open(f).read()
    return content

def get_settings(context):
    """
    Return contents of config.sys file as a dictionary
    """
    try:
        fsys = get_filesys(context)
        #logger.debug("fsys= %s" % fsys)
        fname = "default/config.sys"
        config = _load_file(fsys, fname)
        #logger.debug("config= %s" % config)
        settings_text = config.retrieve()
        #logger.debug("settings_text= %s" % settings_text)
        settings = dict(json.loads(settings_text))
        return settings
    except ContextKeyMissing, e:
        logger.debug('ContextKeyMissing exception')
        raise


def _get_run_info_file(context):
    """
    Returns the actual runinfo data object. If problem, return blank data object
    """
    fsys = get_filesys(context)
    #logger.debug("fsys= %s" % fsys)
    config = _load_file(fsys, "default/runinfo.sys")
    #logger.debug("config= %s" % config)
    return config


def get_run_info(context):
    """
    Returns the content of the run info as file a dict. If problem, return {}
    """
    try:
        fsys = get_filesys(context)
    except ContextKeyMissing:
        return {}
    #logger.debug("fsys= %s" % fsys)
    config = _get_run_info_file(context)
    #logger.debug("config= %s" % config)
    if config:
        settings_text = config.retrieve()
        #logger.debug("runinfo_text= %s" % settings_text)
        res = json.loads(settings_text)
        #logger.debug("res=%s" % dict(res))
        return dict(res)
    return {}


def get_all_settings(context):
    """
    Returns a single dict containing content of config.sys and runinfo.sys
    """
    settings = get_settings(context)
    run_info = get_run_info(context)
    settings.update(run_info)
    settings.update(context)
    return settings


def update_key(key, value, context):
    """
    Updates key from the filesystem runinfo.sys file to a new values
    """
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = _load_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    logger.debug("removing %s" % key)
    settings[key] = value  # FIXME: possible race condition?
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)


def delete_key(key, context):
    """
    Removes key from the filesystem runinfo.sys file
    """
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = _load_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    del settings[key]
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)


def get_fanout(parameter_value_list):
    '''
    total_fanout = 1
    if len(self.threshold) > 1:
        for i in self.threshold:
            total_fanout *= self.threshold[i]
    else:
        total_picks = self.threshold[0]
    '''
    pass


def get_threshold():
    pass


def clear_temp_files(context):
    """
    Deletes "default" files from filesystem
    """
    filesystem = get_filesys(context)
    print "Deleting temporary files ..."
    filesystem.delete_local_filesystem('default')
    print "done."
