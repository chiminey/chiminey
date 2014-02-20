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

from django.contrib.auth.models import User
from django.db.models import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.db import transaction

from chiminey.smartconnectorscheduler import storage
from chiminey.smartconnectorscheduler import models
from chiminey.platform.validate import \
    validate_mytardis_parameters, validate_remote_path
from chiminey.platform.generatekeys import \
    generate_unix_key, generate_cloud_key
from chiminey.platform.configure import \
    configure_nectar_platform, configure_unix_platform

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

logger = logging.getLogger(__name__)

def create_platform(platform_name, username,
                    schema_namespace, parameters):
    logger.debug('create platform')
    missing_params = _retrieve_missing_params(schema_namespace, parameters)
    if missing_params:
        message = 'Cannot create platform parameter set.' \
                  ' Paramteres %s are missing' % missing_params
        return False, message
    parameters['platform_name'] = platform_name
    platform_type = parameters['platform_type']
    _configure_platform(platform_type, username, parameters)
    valid_params, message = _validate_parameters(
        platform_type, parameters, passwd_auth=True)
    if not valid_params:
        return valid_params, message
    key_generated, message = _generate_key(platform_type, parameters)
    if not key_generated:
        return key_generated, message
    remove_password = True
    if 'mytardis' in platform_type:
        remove_password = False #parameters['api_key'] fixme uncomment
    if 'password' in parameters.keys() and remove_password:
        parameters['password'] = ''
    created, message = _db_create_platform(platform_name, username,
                    schema_namespace, parameters)
    return created, message


@transaction.commit_on_success
def _db_create_platform(platform_name, username,
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
            parameters = {'platform_name': paramset.name}
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
    if 'platform_name' not in updated_parameters.keys():
        updated_parameters['platform_name'] = platform_name
    updated_platform_record = dict(current_platform_record)
    updated_platform_record.update(updated_parameters)
    platform_type = current_platform_record['platform_type']
    updated_platform_record['platform_type'] = platform_type
    _configure_platform(platform_type, username, updated_platform_record)
    valid_params, message = _validate_parameters(
        platform_type, updated_platform_record, passwd_auth=True)
    if not valid_params:
        return valid_params, message
    key_generated, message = _generate_key(platform_type, updated_platform_record)
    if not key_generated:
        return key_generated, message
    remove_password = True
    if 'mytardis' in platform_type:
        remove_password = False #parameters['api_key'] fixme uncomment
    if 'password' in updated_platform_record.keys() and remove_password:
        updated_platform_record['password'] = ''
    updated, message = _db_update_platform(platform_name, username, updated_platform_record)
    #TODO: cleanup method
    return updated, message


@transaction.commit_on_success
def _db_update_platform(platform_name, username, updated_parameters):
    message = 'Record updated successfully'
    updated = True
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
        paramset = models.PlatformParameterSet.objects.get(
            name=platform_name, owner=owner)
        if 'platform_name' in updated_parameters.keys():
            paramset.name = updated_parameters['platform_name']
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
    except ObjectDoesNotExist:
        return False, 'Record does not exist'


def _retrieve_missing_params(schema_namespace, parameters):
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


def _configure_platform(platform_type, username, parameters):
    if platform_type == 'nectar' or platform_type == 'csrack':
        configure_nectar_platform(platform_type, username, parameters)
    elif platform_type == 'unix' or platform_type == 'nci':
        configure_unix_platform(platform_type, username, parameters)


def _validate_parameters(platform_type, parameters, passwd_auth=False):
    if platform_type == 'unix' or platform_type == 'nci':
        path_list = [parameters['root_path'], parameters['home_path']]
        return validate_remote_path(path_list, parameters, passwd_auth)
    if platform_type == 'mytardis':
        return validate_mytardis_parameters(parameters)
    return True, 'All valid parameters'


def _generate_key(platform_type, parameters):
    if platform_type == 'nectar' or platform_type == 'csrack':
        return generate_cloud_key(parameters)
    elif platform_type == 'nci' or platform_type == 'unix':
        return generate_unix_key(parameters)
    elif platform_type == 'mytardis':
        return True, ''
    else:
        return False, 'Unknown platform type [%s]' % platform_type


def get_platform_settings(platform_url, username):
    platform_name = platform_url.split('/')[0]
    if platform_name == "local":
        return {"scheme": 'file', 'type': 'local', 'host': '127.0.0.1'}
    record, schema_namespace = retrieve_platform(platform_name, username)
    _update_platform_settings(record)
    record['bdp_username'] = username
    return record


#fixme: in the schema definition, change private_key to private_key_name
def _update_platform_settings(settings):
    #platform_type = os.path.basename(schema_namespace)
    platform_type = settings['platform_type']
    settings['type'] = platform_type
    if platform_type == 'nectar' or platform_type == 'csrack':
        settings['username'] = 'root' #fixme avoid hardcoding
        settings['private_key_name'] = settings['private_key']
        settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                               settings['private_key_path'])
        settings['root_path'] = '/home/ec2-user'  # fixme avoid hardcoding
        settings['scheme'] = 'ssh'

    elif platform_type == 'nci':
        settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                               settings['private_key_path'])
        settings['host'] = settings['ip_address']
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


def get_job_dir(output_storage_settings, offset):
    ip_address = output_storage_settings[u'ip_address']
    job_dir = os.path.join(ip_address, offset)
    return job_dir


def get_scratch_platform():
    #return "file://local@127.0.0.1/"
    return "local/"

