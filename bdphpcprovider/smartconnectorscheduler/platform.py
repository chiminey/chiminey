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

import os
import logging
import boto
import paramiko
import socket
import requests

from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
from requests.auth import HTTPBasicAuth
from django.contrib.auth.models import User
from django.db.models import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.files.base import ContentFile

from bdphpcprovider.smartconnectorscheduler import models, sshconnector
from bdphpcprovider.smartconnectorscheduler import storage


logger = logging.getLogger(__name__)

def create_platform(platform_name, username,
                    schema_namespace, parameters):
    logger.debug('create platform')
    missing_params = retrieve_missing_params(schema_namespace, parameters)
    if missing_params:
        message = 'Cannot create platform parameter set.' \
                  ' Paramteres %s are missing' % missing_params
        return False, message
    platform_type = os.path.basename(schema_namespace)
    parameters['name'] = platform_name
    configure_platform(platform_type, username, parameters)
    valid_params, message = validate_parameters(
        platform_type, parameters, passwd_auth=True)
    if not valid_params:
        return valid_params, message
    key_generated, message = generate_key(platform_type, parameters)
    if not key_generated:
        return key_generated, message
    remove_password = True
    if 'mytardis' in platform_type:
        remove_password = False #parameters['api_key'] fixme uncomment
    if 'password' in parameters.keys() and remove_password:
        parameters['password'] = ''
    created, message = db_create_platform(platform_name, username,
                    schema_namespace, parameters)
    return created, message


@transaction.commit_on_success
def db_create_platform(platform_name, username,
                    schema_namespace, parameters):
    message = 'Record created successfully'
    created = True
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        schema = models.Schema.objects.get(namespace=schema_namespace)
        param_set = models.PlatformParameterSet.objects.create(
            name=platform_name, owner=owner, schema=schema)
        for k, v in parameters.items():
            try:
                param_name = models.ParameterName.objects\
                    .get(schema=schema, name=k)
                models.PlatformParameter.objects\
                    .create(name=param_name, paramset=param_set, value=v)
            except ObjectDoesNotExist as e:
                logger.info('Skipping unrecognized parameter name: %s' % k)
                continue
    except ObjectDoesNotExist, e:
        message = e
        created = False
    except IntegrityError:
        message = 'Record with platform name [%s] already exists' % platform_name
        created = False
    return created, message


def retrieve_platform(platform_name, username):
    parameters = {}
    schema_namespace = ''
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        paramset = models.PlatformParameterSet.objects.get(
            name=platform_name, owner=owner)
        schema_namespace = paramset.schema.namespace
        parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)
        for parameter in parameter_objects:
            parameters[parameter.name.name] = parameter.value
    except ObjectDoesNotExist, e:
        logger.debug(e)
    return parameters, schema_namespace


def retrieve_all_platforms(username, schema_namespace_prefix=''):
    platforms = []
    paramsets = []
    logger.debug('username=%s' % username)
    logger.debug('schema_namespace_prefix=%s' % schema_namespace_prefix)
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        if not schema_namespace_prefix:
            paramsets = models.PlatformParameterSet.objects.filter(owner=owner)
        else:
            schemas = models.Schema.objects.filter(namespace__startswith=schema_namespace_prefix)
            for schema in schemas:
                current_paramsets = models.PlatformParameterSet.objects.filter(
                    owner=owner, schema=schema)
                paramsets.extend(current_paramsets)
        for paramset in paramsets:
            parameters = {'name': paramset.name}
            parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)
            for parameter in parameter_objects:
                parameters[parameter.name.name] = parameter.value
            platforms.append(parameters)
    except ObjectDoesNotExist, e:
        logger.exception(e)
    return platforms


def update_platform(platform_name, username,
                    updated_parameters):
    logger.debug(platform_name)
    logger.debug(updated_parameters)
    current_platform_record, schema_namespace = retrieve_platform(platform_name, username)
    if 'name' not in updated_parameters.keys():
        updated_parameters['name'] = platform_name
    updated_platform_record = dict(current_platform_record)
    updated_platform_record.update(updated_parameters)
    platform_type = os.path.basename(schema_namespace)
    configure_platform(platform_type, username, updated_platform_record)
    valid_params, message = validate_parameters(
        platform_type, updated_platform_record, passwd_auth=True)
    if not valid_params:
        return valid_params, message
    key_generated, message = generate_key(platform_type, updated_platform_record)
    if not key_generated:
        return key_generated, message
    remove_password = True
    if 'mytardis' in platform_type:
        remove_password = False #parameters['api_key'] fixme uncomment
    if 'password' in updated_platform_record.keys() and remove_password:
        updated_platform_record['password'] = ''
    updated, message = db_update_platform(platform_name, username, updated_platform_record)
    #TODO: cleanup method
    return updated, message


@transaction.commit_on_success
def db_update_platform(platform_name, username, updated_parameters):
    message = 'Record updated successfully'
    updated = True
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        paramset = models.PlatformParameterSet.objects.get(
            name=platform_name, owner=owner)
        if 'name' in updated_parameters.keys():
                paramset.name = updated_parameters['name']
                paramset.save()
        for k, v in updated_parameters.items():
            try:
                param_name = models.ParameterName.objects\
                    .get(schema=paramset.schema, name=k)
                platform_param = models.PlatformParameter.objects\
                    .get(name=param_name, paramset=paramset)
                platform_param.value = v
                platform_param.save()
            except ObjectDoesNotExist as e:
                print('Skipping unrecognized parameter name: %s' % k)
                continue
    except ObjectDoesNotExist, e:
        message = e
        updated = False
    except IntegrityError:
        message = 'Record with platform name [%s] already exists' % platform_name
        updated = False
    return updated, message


def delete_platform(platform_name, username):
    #todo: delete all contents that are generated for this platform
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        paramset = models.PlatformParameterSet.objects\
            .get(name=platform_name, owner=owner)
        paramset.delete()
        return True, 'Record deleted successfully'
    except ObjectDoesNotExist, e:
        return False, 'Record does not exist'


def configure_platform(platform_type, username, parameters):
    if platform_type == 'nectar':
        configure_nectar_platform(platform_type, username, parameters)
    elif platform_type == 'unix' or platform_type == 'nci':
        configure_unix_platform(platform_type, username, parameters)


def configure_nectar_platform(platform_type, username, parameters):
    key_name = 'bdp_%s' % parameters['name']
    key_relative_path = '%s.pem' % os.path.join(
        '.ssh', username, platform_type, key_name)
    parameters['private_key'] = key_name
    parameters['private_key_path'] = key_relative_path
    parameters['security_group'] = 'bdp_ssh_group'
    if not parameters['vm_image_size']:
        parameters['vm_image_size'] = 'm1.small'


def configure_unix_platform(platform_type, username, parameters):
    key_name = 'bdp_%s' % parameters['name']
    key_relative_path = os.path.join(
        '.ssh', username, platform_type, key_name)
    parameters['private_key_path'] = key_relative_path


def validate_parameters(platform_type, parameters, passwd_auth=False):
    if platform_type == 'unix' or platform_type == 'nci':
        path_list = [parameters['root_path'], parameters['home_path']]
        return validate_remote_path(path_list, parameters, passwd_auth)
    if platform_type == 'mytardis':
        return validate_mytardis_parameters(parameters)
    return True, 'All valid parameters'


def validate_remote_path(path_list, parameters, passwd_auth=False):
    error_messages = []
    for path in path_list:
        found, message = remote_path_exists(path, parameters, passwd_auth)
        if not found:
            if message not in error_messages:
                error_messages.append(str(message))
    if error_messages:
        return False, ', '.join(error_messages)
    else:
        return True, 'Remote path %s exists' % path_list


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


def retrieve_missing_params(schema_namespace, parameters):
    missing_params = []
    try:
        schema = models.Schema.objects.get(namespace=schema_namespace)
        required_params = models.ParameterName.objects.filter(schema=schema)
        if required_params:
            required_params_names = [x.name for x in required_params]
            missing_params = [x for x in required_params_names if x not in parameters]
    except ObjectDoesNotExist, e:
        logger.debug(e)
    return missing_params


def remote_path_exists(remote_path, parameters, passwd_auth=False):
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
            message = '[%s]: %s, %s' % (remote_path, e.__doc__, e.strerror)
    except Exception, e:
        exists = False
        message = '%s, %s' % (e.__doc__, e.strerror)
    return exists, message


def generate_key(platform_type, parameters):
    if platform_type == 'nectar':
        return generate_nectar_key(parameters)
    elif platform_type == 'nci' or platform_type == 'unix':
        return generate_unix_key(parameters)
    elif platform_type == 'mytardis':
        return True, ''
    else:
        return False, 'Unknown platform type [%s]' % platform_type


def generate_nectar_key(parameters):
    key_generated = True
    message = 'Key generated successfully'
    bdp_root_path = storage.get_bdp_root_path()
    security_group_name = parameters['security_group']
    key_name = parameters['private_key']
    key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    key_dir = os.path.dirname(key_absolute_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    try:
        region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
        connection = boto.connect_ec2(
            aws_access_key_id=parameters['ec2_access_key'],
            aws_secret_access_key=parameters['ec2_secret_key'],
            is_secure=True, region=region,
            port=8773, path="/services/Cloud")
        unique_key = False
        counter = 1
        while not unique_key:
            try:
                if not os.path.exists(os.path.join(key_dir, key_name)):
                    key_pair = connection.create_key_pair(key_name)
                    key_pair.save(key_dir)
                    parameters['private_key'] = key_name
                    parameters['private_key_path'] = os.path.join(os.path.dirname(
                    parameters['private_key_path']), '%s.pem' % key_name)
                    logger.debug('key_pair=%s' % key_pair)
                    unique_key = True
            except EC2ResponseError, e:
                if 'InvalidKeyPair.Duplicate' in e.error_code:
                    key_name = '%s_%d' % (parameters['private_key'], counter)
                    counter += 1
                else:
                    logger.exception(e)
                    raise
        connection.get_all_security_groups([security_group_name])
    except EC2ResponseError as e:
        if 'Unauthorized' in e.error_code:
            key_generated = False
            message = 'Unauthorized access to NeCTAR'
        elif 'SecurityGroupNotFoundForProject' in e.error_code:
            security_group = connection.create_security_group(
                    security_group_name, "SSH security group for the BDP Provider")
            security_group.authorize('tcp', 22, 22, '0.0.0.0/0')
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
        all= "\n%s\n" % public_key_content
        f.close()
        fs = storage.RemoteStorage(settings=storage_settings)
        fs.save(remote_key_path, ContentFile(public_key_content))
        ssh_client = sshconnector.open_connection(parameters['ip_address'], ssh_settings)
        #command = 'cat %s >> %s' % (remote_key_path, authorized_remote_path)
        space = " "
        command = 'echo %s >> %s; echo %s >> %s;  echo %s >> %s' % (
            space, authorized_remote_path, public_key_content,
            authorized_remote_path, space, authorized_remote_path)
        command_out, errs = sshconnector.run_command_with_status(ssh_client, command)
        if errs:
            if 'Permission denied' in errs:
                key_generated = False
                message = 'Permission denied to copy public key to %s/.ssh/authorized_keys' % parameters['home_path']
            else:
                raise IOError
    except sshconnector.AuthError:
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


#fixme: in the schema definition, change private_key to private_key_name
def update_platform_settings(schema_namespace, settings):
    platform_type = os.path.basename(schema_namespace)
    settings['type'] = platform_type
    if platform_type == 'nectar':
        settings['username'] = 'root' #fixme avoid hardcoding
        settings['private_key_name'] = settings['private_key']
        settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                               settings['private_key_path'])
        settings['root_path'] = '/home/centos' #fixme avoid hardcoding
        settings['scheme'] = 'ssh'
    elif platform_type == 'unix':
        settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                               settings['private_key_path'])
        settings['host'] = settings['ip_address']
        settings['scheme'] = 'ssh'
    elif platform_type == 'mytardis':
        settings['mytardis_host'] = settings['ip_address']
        settings['mytardis_user'] = settings['username']
        settings['mytardis_password'] = settings['password']


def get_platform_settings(platform_url, username):
    platform_name = platform_url.split('/')[0]
    record, schema_namespace = retrieve_platform(platform_name, username)
    update_platform_settings(schema_namespace, record)
    return record


def get_job_dir(output_storage_settings, run_settings):
    ip_address = output_storage_settings[u'ip_address']
    offset = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset']
    job_dir = os.path.join(ip_address, offset)
    return job_dir

