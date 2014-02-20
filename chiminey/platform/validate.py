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

import requests
import logging
import os
import paramiko
import socket

from requests.auth import HTTPBasicAuth
from chiminey.smartconnectorscheduler import storage


logger = logging.getLogger(__name__)


def validate_mytardis_parameters(parameters):
    headers = {'Accept': 'application/json'}
    mytardis_url = 'http://%s/api/v1/experiment/?format=json' % parameters['ip_address']
    username = parameters['username']
    password = parameters['password']
    try:
        response = requests.get(mytardis_url, headers=headers,
                                auth=HTTPBasicAuth(username, password))
        status_code = response.status_code
        if status_code == 200:
            return True, "MyTardis instance registered successfully"
        if status_code == 401:
            return False, "Unauthorised access to %s" % parameters['ip_address']
        return False, "MyTardis instance registration failed with %s error code" % response.status_code
    except Exception, e:
        return False, 'Unable to connect to Mytardis instance [%s]' % parameters['ip_address']


def validate_remote_path(path_list, parameters, passwd_auth=False):
    error_messages = []
    for path in path_list:
        found, message = _remote_path_exists(path, parameters, passwd_auth)
        if not found:
            if message not in error_messages:
                error_messages.append(str(message))
    if error_messages:
        return False, ', '.join(error_messages)
    else:
        return True, 'Remote path %s exists' % path_list


def _remote_path_exists(remote_path, parameters, passwd_auth=False):
    password = ''
    if 'password' in parameters.keys():
        password = parameters['password']
    paramiko_settings = {'username': parameters['username'],
                         'password': password}
    if (not passwd_auth) and 'private_key_path' in parameters:
        paramiko_settings['key_filename'] = os.path.join(
            storage.get_bdp_root_path(), parameters['private_key_path'])
    ssh_settings = {'params': paramiko_settings,
                    'host': parameters['ip_address'],
                    'root': "/"}
    exists = True
    message = 'Remote path [%s] exists' % remote_path
    logger.debug("_remote_path_exists")
    try:
        fs = storage.RemoteStorage(settings=ssh_settings)
        fs.listdir(remote_path)
    except paramiko.AuthenticationException, e:
        message = 'Unauthorized access to %s' % parameters['ip_address']
        exists = False
    except socket.gaierror as e:
        exists = False
        if 'Name or service not known' in e:
            message = 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            message = '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
    except IOError, e:
        exists = False
        if 'Permission denied' in e:
            message = "Permission denied to access %s/.ssh " % remote_path
        elif 'No such file' in e:
            message = 'Remote path [%s] does not exist' % remote_path
        else:
            logger.debug("IO ERROR: %s" % e)
            message = '[%s]: %s, %s' % (remote_path, e.__doc__, e.strerror)
    except Exception, e:

        exists = False
        logger.debug("General ERROR: %s" % e)

        message = '%s, %s' % (e.__doc__, e.strerror)
    return exists, message
