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


#fixme change how files are manipulated, use SFTPStorage storage, see hrmcstages.py
def remote_path_exists(remote_path, parameters, passwd_auth=False):
    settings = {'username': parameters['username']}
    if 'password' in parameters:
        settings['password'] = parameters['password']
    if (not passwd_auth) and 'private_key_path' in parameters:
        bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
        settings['private_key'] = os.path.join(bdp_root_path, parameters['private_key_path'])
    logger.debug('settings=%s' % settings)
    logger.debug('parameters=%s' % parameters)
    try:
        ssh_client = sshconnector.open_connection(
            parameters['ip_address'], settings)
        logger.debug("ssh_client=%s" % ssh_client)
        sftp_client = ssh_client.open_sftp()
        sftp_client.listdir_attr(remote_path)
        sftp_client.close()
    except sshconnector.AuthError, e:
        logger.debug(e)
        return False, 'Unauthorized access to %s' % parameters['ip_address']
    except socket.gaierror as e:
        if 'Name or service not known' in e:
            return False, 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            return False, '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
    except IOError, e:
        logger.exception(e)
        if 'Permission denied' in e:
            return False, "Permission denied to access %s/.ssh " % remote_path
        if 'No such file' in e:
            return False, 'Remote path [%s] does not exist' % remote_path
        return False, '[%s]: %s, %s' % (parameters['home_path'], e.__doc__, e.strerror)
    except Exception as e:
        logger.exception(e)
        return False, '%s, %s' % (e.__doc__, e.strerror)
    return True, 'Remote path [%s] exists' % remote_path


def private_key_authenticates(ip_address, username, private_key_path):
    bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
    settings = {'private_key': os.path.join(bdp_root_path, private_key_path),
                'username': username}
    try:
        sshconnector.open_connection(ip_address, settings)
    except sshconnector.AuthError, e:
        return False, 'Failed private key authentication to [%s@%s] with [%s]e' \
                      % (username, ip_address, private_key_path)
    return True, 'Successful private key authentication'


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
        key_created = False
        counter = 1
        while not key_created:
            logger.debug('hi%s' % counter)
            try:
                if not os.path.exists(os.path.join(key_dir, key_name)):
                    key_pair = connection.create_key_pair(key_name)
                    #if os.path.exists(key_absolute_path):
                    #    os.remove(key_absolute_path)
                    key_pair.save(key_dir)
                    key_created = True
                    logger.debug('key_pair=%s' % key_pair)
            except EC2ResponseError, e:
                if 'InvalidKeyPair.Duplicate' in e.error_code:
                    #connection.delete_key_pair(key_name)
                    #logger.debug('old key %s deleted' % key_absolute_path)
                    pass
                else:
                    logger.exception(e)
                    raise
            if not key_created:
                key_name = '%s_%d' % (parameters['private_key'], counter)
                counter += 1

        parameters['private_key'] = key_name
        parameters['private_key_path'] = os.path.join(os.path.dirname(
            parameters['private_key_path']), '%s.pem' % key_name)
        logger.debug('private_key_path=%s' % parameters['private_key_path'])
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
        return False, '%s, %s' % (e.__doc__, e.strerror)
    return True, 'Key generated successfully'


#fixme change how files are manipulated, use SFTPStorage storage, see hrmcstages.py
def generate_unix_key(bdp_root_path, parameters):
    logger.debug('generate_unix_key started')
    key_name_org = os.path.splitext(os.path.basename(parameters['private_key_path']))[0]
    key_name = key_name_org
    settings = {'username': parameters['username'],
                'password': parameters['password']}
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
        ssh_client = sshconnector.open_connection(parameters['ip_address'], settings)
        logger.debug('ssh_client')
        sftp = ssh_client.open_sftp()
        sftp.put(public_key_absolute_path, remote_key_path)
        sftp.close()
        command = 'cat %s >> %s' % (remote_key_path, authorized_remote_path)
        command_out, errs = sshconnector.run_command_with_status(ssh_client, command)
        logger.debug('command_out=%s error=%s' %(command_out, errs))
        if errs:
            if 'Permission denied' in errs:
                return False, "Permission denied to copy public key to %s/.ssh/authorized_keys " % parameters['home_path']
            raise IOError
        logger.debug('command=%s' % command)
    except sshconnector.AuthError:
        message = 'Unauthorized access to %s' % parameters['ip_address']
        return False, message
    except socket.gaierror, e:
        logger.exception(e)
        if 'Name or service not known' in e:
            return False, 'Unknown IP address [%s]' % parameters['ip_address']
        else:
            return False, '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
    except IOError, e:
        #['__doc__', '__getitem__', '__init__', '__module__', '__str__', 'args', 'errno', 'filename', 'strerror']
        if 'Permission denied' in e:
            return False, "Permission denied to copy public key to %s/.ssh " % parameters['home_path']
        if 'No such file' in e:
            return False, 'Home path [%s] does not exist' % parameters['home_path']
        return False, '[%s]: %s, %s' % (parameters['home_path'], e.__doc__, e.strerror)
    except Exception as e:
        logger.exception(e)
        return False, '%s, %s' % (e.__doc__, e.strerror)
    logger.debug('generate_unix_key ended')
    return True, 'Key generated successfully'


def generate_key(platform_type, bdp_root_path, parameters):
    if platform_type == 'nectar':
        return generate_nectar_key(bdp_root_path, parameters)
    elif platform_type == 'nci' or platform_type == 'unix':
        return generate_unix_key(bdp_root_path, parameters)
    else:
        return False, 'Unknown platform type [%s]' % platform_type
    return False, []


def validate_parameters(platform_type, parameters, passwd_auth=False):
    if platform_type == 'unix' or platform_type == 'nci':
            path_list = [parameters['root_path'], parameters['home_path']]
            return validate_remote_path(path_list, parameters, passwd_auth)
    else:
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
    parameters['private_key_path'] = os.path.join(
        '.ssh', username, platform_type, key_name)


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
    failure_message = 'RECORD CREATE FAILURE:'
    if not params_present:
        message = 'Cannot create platform parameter set.' \
                  ' Required params= %s  Provided params= %s '\
                  % (required_params, provided_params)
        logger.debug(message)
        return False, '%s %s' % (failure_message, message)

    platform_type = os.path.basename(schema_namespace)
    configure_platform(platform_type, username, parameters)
    #filters = dict(parameters)
    logger.debug('here=%s' % parameters)
    filters = {'name': parameters['name']}
    unique = is_unique_platform_paramset(
                platform, schema, filters)
    if not unique:
        return unique, '%s Record with platform name [%s] already exists' % (failure_message, parameters['name'])
    logger.debug('here')
    valid_params, message = validate_parameters(
        platform_type, parameters, passwd_auth=True)
    if not valid_params:
        return valid_params, '%s %s' % (failure_message, message)

    bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
    key_generated, message = generate_key(platform_type, bdp_root_path, parameters)
    logger.debug('there')

    if not key_generated:
        return key_generated, '%s %s' % (failure_message, message)

    if 'password' in parameters.keys():
        parameters['password'] = ''
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
    return True, 'Record created successfully'


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
    logger.debug('filters=%s' %filters)
    logger.debug(updated_params)
    platform, schema = get_platform_and_schema(username, schema_namespace)
    failure_message = 'RECORD UPDATE FAILURE:'
    if not required_param_exists(schema, updated_params):
        message = 'Keys in updated_parameters are unknown'
        logger.debug(message)
        return False,'%s %s' % (failure_message, message)
    if not required_param_exists(schema, filters):
        message = 'Keys in filters are unknown'
        logger.debug(message)
        return False, '%s %s' % (failure_message, message)
    new_filters = {'name': updated_params['name']}
    logger.debug(new_filters)
    #new_filters.update(updated_params)
    if not is_unique_platform_paramset(platform, schema, new_filters):
        message = 'Record with platform name [%s] already exists' % updated_params['name']
        logger.debug(filters)
        logger.debug(updated_params)



        #fixme assumes filters n updated_params represent all params. works only with gui
        if updated_params['name'] == filters['name']:
            for k, v in filters.items():
                if updated_params[k] != filters[k] and (k != 'password'):
                    break
            else:
                return True, 'No change made to the record'
        else:
            return False, '%s %s' % (failure_message, message)

        #return True, 'Record updated successfully'
    current_record = {'name': filters['name']}
    param_sets = filter_platform_paramsets(platform, schema, current_record)
    if len(param_sets) > 1:
        message = 'Multiple records found. Add more parameters to filters'
        logger.debug(message)
        return False, '%s %s' % (failure_message, message)
    platform_parameters = models.PlatformInstanceParameter\
        .objects.filter(paramset=param_sets[0])
    #keys = [k for k, v in updated_params.items()]
    existing_params = {}
    expected_params = {}
    for platform_parameter in platform_parameters:
        name = platform_parameter.name.name
        existing_params[name] = platform_parameter.value
        if name in updated_params.keys():
            if name != 'password':
                platform_parameter.value = updated_params[name]
            else:
                platform_parameter.value = ''
        expected_params[name] = platform_parameter.value
    if 'password' in updated_params.keys():
        expected_params['password'] = updated_params['password']
    logger.debug('existing_params=%s' % existing_params)
    logger.debug('expected_params=%s' % expected_params)
    platform_type = os.path.basename(schema_namespace)
    regenerate_key = False
    if platform_type == 'nectar':
        if existing_params['ec2_access_key'] != expected_params['ec2_access_key']:
            regenerate_key = True
        if existing_params['ec2_secret_key'] != expected_params['ec2_secret_key']:
            regenerate_key = True
        #new_key_path = os.path.join(os.path.dirname(existing_params['private_key_path']),
        #                            '%s.pem' % expected_params['username'])
    elif platform_type == 'unix' or platform_type == 'nci':
        if existing_params['ip_address'] != expected_params['ip_address']:
            regenerate_key = True
        if existing_params['username'] != expected_params['username']:
            #new_key_path = os.path.join(os.path.dirname(existing_params['private_key_path']),
            #                        expected_params['username'])
            regenerate_key = True
    #logger.debug(expected_params['password'])
    if regenerate_key:
        #if 'private_key_path' in expected_params:
        #    expected_params['private_key_path'] = new_key_path
        bdp_root_path = '/var/cloudenabling/remotesys' #fixme replace by parameter
        key_generated, message = generate_key(platform_type, bdp_root_path, expected_params)
        if not key_generated:
            return key_generated,'%s %s' % (failure_message, message)
    if 'password' in expected_params.keys():
        expected_params['password'] = ''


    valid_params, message = validate_parameters(
        platform_type, expected_params)
    if not valid_params:
        return valid_params,'%s %s' % (failure_message, message)

    for platform_parameter in platform_parameters:
        platform_parameter.save()
    message = 'Record updated successfully'
    return True, message


#todo: delete all contents that are generated for this platform
def delete_platform_paramsets(username, schema_namespace, filters):
    failure_message = 'RECORD DELETE FAILURE:'
    if not filters:
        logger.debug('Filter should not be empty. Exiting...')
        return
    platform, schema = get_platform_and_schema(username, schema_namespace)
    current_record = {'name': filters['name']}
    param_sets = filter_platform_paramsets(platform, schema, current_record)
    for param_set in param_sets:
        logger.debug('deleting ... %s' % param_set)
        param_set.delete()
    logger.debug("%d platforms are deleted" % len(param_sets))
    if len(param_sets):
        message = 'Record deleted successfully'
        return True, message
    else:
        message = 'Record does not exist'
        return False, '%s %s' % (failure_message, message)


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
    #if not required_param_exists(schema, filters):
    #    return []
    all_param_sets = []
    #fixme temporary code to enter only unique parameter name
    platforms = models.PlatformInstance.objects.all()
    for platform in platforms:
        schema_namespace = platform.schema_namespace_prefix
        schema, _ = models.Schema.objects.get_or_create(namespace=schema_namespace)
        param_sets = models.PlatformInstanceParameterSet\
            .objects.filter(platform=platform)
        for k, v in filters.items():
            if k == 'password':
                continue
            #logger.debug('k=%s, v=%s' % (k, v))
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
                logger.debug('Analysing %s %s' % (param_set.pk, schema_namespace))
                try:
                    models.PlatformInstanceParameter.objects.get(
                        name=param_name, paramset=param_set, value=v)
                    potential_paramsets.append(param_set)
                except ObjectDoesNotExist as e:
                    logger.debug('%s is removed' % param_set.pk)
                except Exception:
                    raise
            param_sets = list(potential_paramsets)
            all_param_sets.extend(param_sets)
            logger.debug('param_sets=%s' % param_sets)
            logger.debug('all_param_sets=%s' % all_param_sets)
    return all_param_sets

#fixme rename to get_platform_credentials
def get_credentials(settings):
    credentials = {}
    try:
        platform_type = settings['type']
        credentials['type'] = platform_type
        if platform_type == 'nectar':
            credentials['username'] = 'root' #fixme acoid hardcoding
            credentials['private_key'] = settings['private_key_path']
            credentials['root_path'] = '/home/centos' #fixme avoid hardcoding
            credentials['ec2_access_key'] = settings['ec2_access_key']
            credentials['ec2_secret_key'] = settings['ec2_secret_key']
    except KeyError, e:
        logger.debug(e)
        raise
    return credentials

#fixme rename to retrienve_platform_record
def retrieve_platform(platform_name):
    filter = {'name': platform_name}
    param_sets = filter_platform_paramsets('', '', filter)
    record = {}
    if not len(param_sets):
        return record
    if len(param_sets) > 1:
        return record
    schema = param_sets[0].schema.namespace
    platform_params = {}
    parameters = models.PlatformInstanceParameter\
        .objects.filter(paramset=param_sets[0])
    for param in parameters:
        name = param.name.name
        platform_params[name] = param.value
    platform_params['type'] = os.path.basename(schema)
    record = platform_params
    return record

#fixme rewrite this after a model with unique key, based on platform name, is implemented
def get_platform_name(username, schema_namespace):
    platform, schema = get_platform_and_schema(username, schema_namespace)
    if not (platform and schema):
        return ''
    param_sets = models.PlatformInstanceParameterSet\
            .objects.filter(platform=platform)
    if not param_sets:
        return ''
    param_name = models.ParameterName.objects.get(
                    schema=schema, name='name')
    platform_param_instantce = \
        models.PlatformInstanceParameter.objects.filter(
                        name=param_name, paramset=param_sets[0])
    if not platform_param_instantce:
        return ''
    return platform_param_instantce[0].value


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
