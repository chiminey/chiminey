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


def get_settings(context):
    """
    Return contents of config.sys file as a dictionary
    """
    try:
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)
        fname = "default/config.sys"
        config = _load_file(fsys, fname)
        print("config= %s" % config)
        settings_text = config.retrieve()
        print("settings_text= %s" % settings_text)
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
    logger.debug("fsys= %s" % fsys)
    config = _load_file(fsys, "default/runinfo.sys")
    logger.debug("config= %s" % config)
    return config


def get_run_info(context):
    """
    Returns the content of the run info as file a dict. If problem, return {}
    """
    try:
        fsys = get_filesys(context)
    except ContextKeyMissing:
        return {}
    logger.debug("fsys= %s" % fsys)
    config = _get_run_info_file(context)
    logger.debug("config= %s" % config)
    if config:
        settings_text = config.retrieve()
        logger.debug("runinfo_text= %s" % settings_text)
        res = json.loads(settings_text)
        logger.debug("res=%s" % dict(res))
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


def clear_temp_files(context):
    """
    Deletes "default" files from filesystem
    """
    filesystem = get_filesys(context)
    print "Deleting temporary files ..."
    filesystem.delete_local_filesystem('default')
    print "done."
