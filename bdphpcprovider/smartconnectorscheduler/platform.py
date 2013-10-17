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
from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError

from django.contrib.auth.models import User
from bdphpcprovider.smartconnectorscheduler import models
from django.db.models import ObjectDoesNotExist

from bdphpcprovider.smartconnectorscheduler import sshconnector

logger = logging.getLogger(__name__)


def remote_path_exists(remote_path, parameters):
    try:
        ssh_client = sshconnector.open_connection(parameters['ip_address'], parameters)
        sftp_client = ssh_client.open_sftp()
        sftp_client.listdir_attr(remote_path)
        sftp_client.close()
    except IOError, e:
        logger.exception(e)
        return False, 'Remote path [%s] does not exist' % remote_path
    except sshconnector.AuthError:
            return False, 'Unauthorized access to %s' % parameters['ip_address']
    except socket.gaierror as e:
        if 'Name or service not known' in e:
            return False, 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            raise
    return True, 'Remote path [%s] exists' % remote_path


def private_key_authenticates(ip_address, username, private_key_path):
    settings = {'private_key': private_key_path,
                'username': username}
    try:
        sshconnector.open_connection(ip_address, settings)
    except sshconnector.AuthError, e:
        return False, 'Failed private key authentication with [%s]e' \
                      % private_key_path
    return True, 'Successful private key authentication'


#fixme change how files are manipulated, use NFS storage upload??
def generate_nectar_key(bdp_root_path, parameters):
    security_group_name = parameters['security_group']
    key_name = parameters['private_key']
    key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    key_dir = os.path.dirname(key_absolute_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    try:
        region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
        logger.debug('region.name=%s' % region.name)
        logger.debug('ec2 access key=%s' % parameters['ec2_access_key'])
        logger.debug('ec2 secret key=%s' % parameters['ec2_secret_key'])
        connection = boto.connect_ec2(
            aws_access_key_id=parameters['ec2_access_key'],
            aws_secret_access_key=parameters['ec2_secret_key'],
            is_secure=True, region=region,
            port=8773, path="/services/Cloud")
        logger.debug('connection=%s' % connection)
        if os.path.exists(key_absolute_path):
            os.remove(key_absolute_path)
        try:
            key_pair = connection.create_key_pair(key_name)
            key_pair.save(key_dir)
            logger.debug('key_pair=%s' % key_pair)
        except EC2ResponseError, e:
            if 'InvalidKeyPair.Duplicate' in e.error_code:
                connection.delete_key_pair(key_name)
                logger.debug('old key %s deleted' % key_absolute_path)
                key_pair = connection.create_key_pair(key_name)
                key_pair.save(key_dir)
                logger.debug('key_pair=%s' % key_pair)
        connection.get_all_security_groups([security_group_name])
    except EC2ResponseError as e:
        if 'Unauthorized' in e.error_code:
            message = 'Unauthorized access to NeCTAR'
            return False, message
        elif 'SecurityGroupNotFoundForProject' in e.error_code:
            security_group = connection.create_security_group(
                    security_group_name, "SSH security group for the BDP Provider")
            security_group.authorize('tcp', 22, 22, '0.0.0.0/0')
            logger.debug('%s created' % security_group)
        else:
            logger.debug('=%s' % e.__dict__)
            return False, e.error_code
    except Exception as e:
        logger.debug(e)
        raise
    return True, 'Key generated successfully'


#fixme change how files are manipulated, use NFS storage upload??
def generate_unix_key(bdp_root_path, parameters):
    key_name = os.path.splitext(os.path.basename(parameters['private_key_path']))[0]
    remote_key_path = os.path.join(parameters['home_path'], '.ssh', ('%s.pub' % key_name))
    authorized_remote_path = os.path.join(parameters['home_path'], '.ssh', 'authorized_keys')
    settings = {'username': parameters['username'],
                'password': parameters['password']}
    private_key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
    public_key_absolute_path = '%s.pub' % private_key_absolute_path
    key_dir = os.path.dirname(private_key_absolute_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
    try:
        private_key = paramiko.RSAKey.generate(1024)
        private_key.write_private_key_file(private_key_absolute_path)
        public_key = paramiko.RSAKey(filename=private_key_absolute_path)
        public_key_content = '%s %s' % (public_key.get_name(), public_key.get_base64())
        f = open(public_key_absolute_path, 'w')
        f.write(public_key_content)
        f.close()
        ssh_client = sshconnector.open_connection(parameters['ip_address'], settings)
        sftp = ssh_client.open_sftp()
        sftp.put(public_key_absolute_path, remote_key_path)
        sftp.close()
        command = "cat %s >> %s" % (remote_key_path, authorized_remote_path)
        command_out, errs = sshconnector.run_command_with_status(ssh_client, command)
        logger.debug('command_out=%s' % command_out)
    except sshconnector.AuthError:
        message = 'Unauthorized access to %s' % parameters['ip_address']
        return False, message
    except socket.gaierror, e:
        logger.exception(e)
        if 'Name or service not known' in e:
            return False, 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            raise
    except IOError, e:
        logger.exception(e)
        return False, 'Home path [%s] does not exist' % parameters['home_path']
    except Exception as e:
        logger.exception(e)
        raise
    return True, 'Key generated successfully'


def generate_key(platform_type, bdp_root_path, parameters):
    if platform_type == 'nectar':
        return generate_nectar_key(bdp_root_path, parameters)
    elif platform_type == 'nci' or platform_type == 'ssh':
        return generate_unix_key(bdp_root_path, parameters)
    else:
        return False, 'Unknown platform type [%s]' % platform_type
    return False, []


#fixme deprecate this method. No need for filter; we have unique keys
#fixme refactor this code
#fixme call different create methods for different platforms
def create_platform_paramset(username, schema_namespace,
                             parameters, filter_keys=None):
    logger.debug('create platform')
    owner = get_owner(username)
    platform, _ = models.PlatformInstance.objects.get_or_create(
       owner=owner, schema_namespace_prefix=schema_namespace)
    schema, _ = models.Schema.objects.get_or_create(namespace=schema_namespace)
    params_present, provided_params, required_params = \
        all_params_present(schema, parameters)
    if not params_present:
        logger.debug('Cannot create platform parameter set.'
                     '\n Required params= %s  \n Provided params= %s '
                     % (required_params, provided_params))
        return False
    platform_type = os.path.basename(schema_namespace)
    bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
    key_name = 'bdp_%s' % parameters['name']
    key_relative_path = os.path.join(
            '.ssh', username, platform_type, key_name)
    if platform_type == 'nectar':
        security_group_name = 'bdp_ssh_group'
        key_relative_path = '%s.pem' % key_relative_path
        parameters['private_key'] = key_name
        parameters['private_key_path'] = key_relative_path
        parameters['security_group'] = security_group_name
        if not parameters['vm_image_size']:
            parameters['vm_image_size'] = 'm1.small'
    elif platform_type == 'nci' or platform_type == 'ssh':
        parameters['private_key_path'] = key_relative_path
    filters = dict(parameters)
    unique = is_unique_platform_paramset(
                platform, schema, filters)
    logger.debug('unique parameter set %s' % unique)
    key_generated = False
    if unique:
        if platform_type == 'nci' or platform_type == 'ssh':
            path_exists, message = remote_path_exists(parameters['root_path'], parameters)
            if not path_exists:
                return path_exists, message
            path_exists, message = remote_path_exists(parameters['home_path'], parameters)
            if not path_exists:
                return path_exists, message
        key_generated, message = generate_key(platform_type, bdp_root_path, parameters)
    else:
        message = 'Record already exists'
    if key_generated:
         param_set = models.PlatformInstanceParameterSet.objects\
             .create(platform=platform, schema=schema)
         for k, v in parameters.items():
            try:
                param_name = models.ParameterName.objects\
                    .get(schema=schema, name=k)
            except ObjectDoesNotExist as e:
                logger.debug('Skipping unrecognized parameter name: %s' % k)
                continue
            models.PlatformInstanceParameter.objects\
                .get_or_create(name=param_name, paramset=param_set, value=v)
            message = 'Record created successfully'
         return True, message
    else:
        return False, message
    logger.debug(message)
    return False, message


def retrieve_platform_paramsets(username, schema_namespace):
    recorded_platforms = []
    owner = get_owner(username)
    if not owner:
        logger.debug('username=%s unknown' % username)
        return recorded_platforms
    platforms = models.PlatformInstance.objects.filter(
       owner=owner, schema_namespace_prefix__startswith=schema_namespace)
    for platform in platforms:
        platform_type = os.path.basename(platform.schema_namespace_prefix)
        param_sets = models.PlatformInstanceParameterSet\
            .objects.filter(platform=platform)
        for param_set in param_sets:
            platform_parameters = models.PlatformInstanceParameter\
                .objects.filter(paramset=param_set)
            platform_record = {}
            for platform_parameter in platform_parameters:
                platform_record[platform_parameter.name.name] = platform_parameter.value
            platform_record['type'] = platform_type
            recorded_platforms.append(platform_record)
    return recorded_platforms


def update_platform_paramset(username, schema_namespace,
                             filters, updated_params):
    platform, schema = get_platform_and_schema(username, schema_namespace)
    if not required_param_exists(schema, updated_params):
        message = 'Keys in updated_parameters are unknown'
        logger.debug(message)
        return False, message
    if not required_param_exists(schema, filters):
        message = 'Keys in filters are unknown'
        logger.debug(message)
        return False, message
    new_filters = dict(filters)
    new_filters.update(updated_params)
    if not is_unique_platform_paramset(platform, schema, new_filters):
        message = 'Record exists with the updated parameters'
        logger.debug(message)
        return False, message
    param_sets = filter_platform_paramsets(platform, schema, filters)
    if len(param_sets) != 1:
        message = 'Multiple records found. Add more parameters to filters'
        logger.debug(message)
        return False, message
    platform_parameters = models.PlatformInstanceParameter\
        .objects.filter(paramset=param_sets[0])
    keys = [k for k, v in updated_params.items()]
    for platform_parameter in platform_parameters:
        name = platform_parameter.name.name
        if name in keys:
            platform_parameter.value = updated_params[name]
            platform_parameter.save()
    message = 'Record updated successfully'
    return True, message


def delete_platform_paramsets(username, schema_namespace, filters):
    if not filters:
        logger.debug('Filter should not be empty. Exiting...')
        return
    platform, schema = get_platform_and_schema(username, schema_namespace)
    param_sets = filter_platform_paramsets(platform, schema, filters)
    for param_set in param_sets:
        logger.debug('deleting ... %s' % param_set)
        param_set.delete()
    logger.debug("%d platforms are deleted" % len(param_sets))
    if len(param_sets):
        message = 'Record deleted successfully'
        return True, message
    else:
        message = 'Record does not exist'
        return False, message


def is_unique_platform_paramset(platform, schema, filters):
    if not filters:
        logger.debug('Filter field should not be empty. Exiting...')
        return False
    param_sets = filter_platform_paramsets(
        platform, schema, filters)
    if param_sets:
        return False
    return True


def filter_platform_paramsets(platform, schema, filters):
    if not required_param_exists(schema, filters):
        return []
    param_sets = models.PlatformInstanceParameterSet\
        .objects.filter(platform=platform)
    for k, v in filters.items():
        logger.debug('k=%s, v=%s' % (k, v))
        try:
            param_name = models.ParameterName.objects.get(
                schema=schema, name=k)
        except ObjectDoesNotExist as e:
            logger.debug('Skipping unrecognized parametername: %s' % k)
            continue
        except Exception:
            raise
        potential_paramsets = []
        for param_set in param_sets:
            logger.debug('Analysing %s' % param_set.pk)
            try:
                models.PlatformInstanceParameter.objects.get(
                    name=param_name, paramset=param_set, value=v)
                potential_paramsets.append(param_set)
            except ObjectDoesNotExist as e:
                logger.debug('%s is removed' % param_set.pk)
            except Exception:
                raise
        param_sets = list(potential_paramsets)
    return param_sets


def get_owner(username):
    owner = None
    try:
        user = User.objects.get(username=username)
        owner = models.UserProfile.objects.get(user=user)
    except ObjectDoesNotExist as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
        raise
    return owner


def get_platform_and_schema(username, schema_namespace):
    platform = None
    schema = None
    owner = get_owner(username)
    if owner:
        try:
            platform = models.PlatformInstance.objects.get(
                owner=owner, schema_namespace_prefix=schema_namespace)
            schema = models.Schema.objects.get(namespace=schema_namespace)
        except ObjectDoesNotExist as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
            raise
    return (platform, schema)


def all_params_present(schema, parameters):
    required_params = models.ParameterName.objects.filter(schema=schema)
    if required_params:
        required_params_names = [x.name for x in required_params]
        provided_params_names = [x for x in required_params_names if x in parameters]
        if len(provided_params_names) == len(required_params_names):
            return True, provided_params_names, required_params_names
        return False, provided_params_names, required_params_names
    return False, [], []


def required_param_exists(schema, parameters):
    _, params, _ = all_params_present(schema, parameters)
    if params:
        return True
    return False
