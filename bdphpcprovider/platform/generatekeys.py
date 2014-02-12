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

import os
import paramiko
import logging
import socket

from django.core.files.base import ContentFile
from bdphpcprovider.smartconnectorscheduler import storage
from bdphpcprovider.sshconnection import open_connection, AuthError
from bdphpcprovider.compute import run_command_with_status
from bdphpcprovider.cloudconnection import create_ssh_security_group, create_key_pair, EC2ResponseError


logger = logging.getLogger(__name__)


def generate_cloud_key(parameters):
    logger.debug('generating key')
    key_generated = True
    message = 'Key generated successfully'
    bdp_root_path = storage.get_bdp_root_path()
    key_name = parameters['private_key']
    key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    key_dir = os.path.dirname(key_absolute_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    try:
        platform_type = parameters['platform_type']
        logger.debug('platform_type=%s' % platform_type)
        parameters['key_dir'] = key_dir

        if platform_type == 'csrack' or platform_type == 'nectar':
            create_key_pair(parameters)
            create_ssh_security_group(parameters)
        else:
            return False, 'Unknown cloud platform'
    except EC2ResponseError as e:
        if 'Unauthorized' in e.error_code:
            key_generated = False
            message = 'Unauthorized access to %s' % platform_type
        else:
            key_generated = False
            message = e.error_code
    except Exception as e:
        key_generated = False
        message = e
    return key_generated, message


def generate_unix_key(parameters):
    key_generated = True
    message = 'Key generated successfully'
    password = ''
    if 'password' in parameters.keys():
        password = parameters['password']

    ssh_settings = {'username': parameters['username'],
                'password': password}

    storage_settings = {'params': ssh_settings,
                        'host': parameters['ip_address'],
                        'root': "/"}
    bdp_root_path = storage.get_bdp_root_path()
    key_name_org = os.path.splitext(os.path.basename(parameters['private_key_path']))[0]
    key_name = key_name_org
    private_key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    key_dir = os.path.dirname(private_key_absolute_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    counter = 1
    while os.path.exists(os.path.join(key_dir, key_name)):
        key_name = '%s_%d' % (key_name_org, counter)
        counter += 1
    parameters['private_key_path'] = os.path.join(os.path.dirname(
            parameters['private_key_path']), key_name)
    private_key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    public_key_absolute_path = '%s.pub' % private_key_absolute_path
    remote_key_path = os.path.join(parameters['home_path'], '.ssh', ('%s.pub' % key_name))
    authorized_remote_path = os.path.join(parameters['home_path'], '.ssh', 'authorized_keys')
    try:
        private_key = paramiko.RSAKey.generate(1024)
        private_key.write_private_key_file(private_key_absolute_path)
        public_key = paramiko.RSAKey(filename=private_key_absolute_path)
        public_key_content = '%s %s' % (public_key.get_name(), public_key.get_base64())
        f = open(public_key_absolute_path, 'w')
        f.write("\n%s\n" % public_key_content)
        f.close()
        fs = storage.RemoteStorage(settings=storage_settings)
        fs.save(remote_key_path, ContentFile(public_key_content))
        ssh_client = open_connection(parameters['ip_address'], ssh_settings)
        #command = 'cat %s >> %s' % (remote_key_path, authorized_remote_path)
        space = " "
        command = 'echo %s >> %s; echo %s >> %s;  echo %s >> %s; chmod 600 %s' % (
            space, authorized_remote_path, public_key_content,
            authorized_remote_path, space, authorized_remote_path,
            authorized_remote_path)
        command_out, errs = run_command_with_status(ssh_client, command)
        if errs:
            if 'Permission denied' in errs:
                key_generated = False
                message = 'Permission denied to copy public key to %s/.ssh/authorized_keys' % parameters['home_path']
            else:
                raise IOError
    except AuthError:
        key_generated = False
        message = 'Unauthorized access to %s' % parameters['ip_address']
    except socket.gaierror, e:
        key_generated = False
        if 'Name or service not known' in e:
            message = 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            message = '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
    except IOError, e:
        key_generated = False
        if 'Permission denied' in e:
            message = "Permission denied to copy public key to %s/.ssh " % parameters['home_path']
        elif 'No such file' in e:
            message = 'Home path [%s] does not exist' % parameters['home_path']
        else:
            message = '[%s]: %s, %s' % (parameters['home_path'], e.__doc__, e.strerror)
    except Exception as e:
        key_generated = False
        message = e
    return key_generated, message

