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

import boto
import time
import logging
import os

from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
from django.conf import settings as django_settings
from chiminey.cloudconnection.errors import\
    VMNotFoundError, UnknownCloudProviderError,\
    CreatingVMFailedError

logger = logging.getLogger(__name__)
NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']


def create_vms(settings):
    """
        Create vms and return ip_address
    """
    all_vms = []
    try:
        platform_type = settings['platform_type']
        if platform_type in django_settings.VM_IMAGES:
            params = django_settings.VM_IMAGES[platform_type]
            placement = params['placement']
            vm_image = params['vm_image']
            user_data=params['user_data']
        else:
            raise UnknownCloudProviderError
        connection = _create_cloud_connection(settings)
        logger.info("Creating %d VM(s)" % settings['max_count'])
        reservation = connection.run_instances(
                    placement=placement,
                    image_id=vm_image,
                    min_count=settings['min_count'],
                    max_count=settings['max_count'],
                    user_data=user_data,
                    key_name=settings['private_key_name'],
                    security_groups=[settings['security_group']],
                    instance_type=settings['vm_image_size'])
        logger.debug("Created Reservation %s" % reservation)
        instances = reservation.instances
        logger.debug("instances=%s" % str(instances))
        for vm in instances:
            logger.debug("vm=%s" % vm)
            all_vms.append(vm)
    except IndexError, e:
        logger.error("cannot load vm parameters")
    except UnknownCloudProviderError, e:
        logger.error("unknown cloud provider")
        logger.debug(e)
    except EC2ResponseError as e:
        logger.error(e)
        logger.debug('error_code=%s' % e.error_code)
        logger.error(e.message)
        if 'TooManyInstances' not in e.error_code:
            logger.debug(e)
            raise
    except Exception:
        raise CreatingVMFailedError
    logger.debug(all_vms)
    logger.debug('%d of %d requested VM(s) created'
                 % (len(all_vms), settings['max_count']))
    return all_vms


def destroy_vms(settings, all_vms):
    """
        Terminate
            - all vms, or
            - a group of vms, or
            - a single vm
    """
    terminated_vms = []
    if not all_vms:
        logging.error("No running vm(s)")
        return terminated_vms
    logger.info("Terminating %d vm(s)" % len(all_vms))
    connection = _create_cloud_connection(settings)
    for vm in all_vms:
        try:
            instance_list = connection.terminate_instances(
                instance_ids=[vm.id])
            terminated_vms.append(instance_list[0])
        except Exception as e:
            logger.debug(e)
    return terminated_vms


def wait_for_vms_to_start_running(all_vms, settings):
    all_running_vms = []
    # FIXME: add final timeout for when VMs fail to initialise properly
    # TODO: spamming all nodes in tenancy continually is impolite, so should
    # store nodes we know to be part of this run (in context?)
    #todo: cleanup nodes that are spawning indefinitely (timeout)
    logger.debug("Started waiting")
    #maximum rwait time 3 minutes
    minutes = 10 #fixme avoid hard coding; move to settings.py
    max_retries = (minutes * 60)/settings['cloud_sleep_interval']
    logger.debug("max_retries=%s" % max_retries)
    retries = 0
    while all_vms:
        for vm in list(all_vms):
            ip_address = vm.ip_address
            if not ip_address:
                ip_address = vm.private_ip_address
            logger.debug("#%s this vm %s" % (retries, vm))
            if _does_vm_exist(vm):
                logger.debug("exists")
                if is_vm_running(vm):
                    logger.debug("isrunning")
                    all_running_vms.append(vm)
                    all_vms.remove(vm)
            else:
                logger.debug("not exist")
                all_vms.remove(vm)
            logger.debug('Current status of %s: %s' % (ip_address, vm.state))
            if vm.state in 'error':
                logger.debug("error")
                all_vms.remove(vm)
            if  retries == max_retries:
                logger.debug("timeout")
                break
            logger.debug("finished check")
        retries += 1
        logger.debug("sleeping")
        time.sleep(settings['cloud_sleep_interval'])
    return all_running_vms


def wait_for_vms_to_terminate(all_vms, settings):
    logger.debug('remaining_vms=%s' % all_vms)
    while all_vms:
        for vm in all_vms:
            current_vm = vm
            ip_address = vm.ip_address
            if not ip_address:
                ip_address = vm.private_ip_address
            if _is_vm_terminated(current_vm):
                all_vms.remove(vm)
                logger.debug('Current status of %s: %s' % (ip_address, 'terminated'))
                logger.debug('remaining_vms=%s' % all_vms)
            else:
                logger.debug('Current status of %s: %s' % (ip_address, vm.state))
        time.sleep(settings['cloud_sleep_interval'])


def get_this_vm(vm_id, settings):
    connection = _create_cloud_connection(settings)
    logger.debug("cc=%s" % connection)
    try:
        reservation_list = connection.get_all_instances(
            instance_ids=[vm_id], filters=None)
        logger.debug("reservation_list=%s" % reservation_list)
        logger.debug("reservation_list[0]=%s" % reservation_list[0])
        logger.debug("reservation_list[0].instances=%s" % reservation_list[0].instances)

        for i in reservation_list[0].instances:
            logger.debug("i=%s" % i)
            if i.id in vm_id:
                return i
    except Exception as e:
        logger.debug('caught %s '% e)
        logger.debug(e)
        raise VMNotFoundError


def get_vm_ip(vm_id, settings):
    connection = _create_cloud_connection(settings)
    try:
        reservation_list = connection.get_all_instances(
            instance_ids=[vm_id], filters=None)
        for vm in reservation_list[0].instances:
            if vm.id is vm_id:
                ip_address = vm.ip_address
                if not ip_address:
                    ip_address = vm.private_ip_address
                return ip_address
    except Exception, e:
        logger.debug(e)
        raise VMNotFoundError


def is_vm_running(vm):
    """
        Checks whether a vm with @vm_id
        is running or not
    """
    try:
        vm.update()
        if vm.state in 'running':
            return True
    except EC2ResponseError, e:
        logger.debug(e)
    return False


def get_running_vms(settings):
    all_vms = _get_all_vms(settings)
    running_vms = []
    for vm in all_vms:
        if is_vm_running(vm):
            running_vms.append(vm)
    return running_vms

def create_key_pair(settings):
    connection = _create_cloud_connection(settings)
    unique_key = False
    counter = 1
    key_name = settings['private_key']
    key_dir = settings['key_dir']
    while not unique_key:
        try:
            if not os.path.exists(os.path.join(key_dir, key_name)):
                key_pair = connection.create_key_pair(key_name)
                key_pair.save(key_dir)
                settings['private_key'] = key_name
                logger.debug('key_pair=%s' % key_pair)
                unique_key = True
        except EC2ResponseError, e:
            if 'InvalidKeyPair.Duplicate' in e.error_code:
                pass
            else:
                logger.exception(e)
                raise
        key_name = '%s_%d' % (settings['private_key'], counter)
        counter += 1
    settings['private_key_path'] = os.path.join(
        os.path.dirname(settings['private_key_path']),
        '%s.pem' % settings['private_key'])


def create_ssh_security_group(settings):
    connection = _create_cloud_connection(settings)
    security_group_name = settings['security_group']
    try:
        if not connection.get_all_security_groups([security_group_name]):
            _create_ssh_group(connection, security_group_name)
    except EC2ResponseError as e:
        if 'SecurityGroupNotFoundForProject' in e.error_code:
            _create_ssh_group(connection, security_group_name)
        elif 'InvalidGroup.NotFound' in e.error_code:
            _create_ssh_group(connection, security_group_name)
        else:
            logger.exception(e)
            raise


def _create_ssh_group(connection, security_group_name):
    security_group = connection.create_security_group(
        security_group_name, "SSH security group of the BDP HPC Provider")
    security_group.authorize('tcp', 22, 22, '0.0.0.0/0')


def _create_cloud_connection(settings):
    provider = settings['platform_type']
    logger.debug('provider=%s' % provider)
    if provider.lower() == "amazon":
        return _create_amazon_connection(settings)
    elif provider.lower() == "nectar":
        return _create_nectar_connection(settings)
    elif provider.lower() == 'csrack':
        return _create_csrack_connection(settings)
    else:
        logger.info("Unknown provider: %s" % provider)
        raise UnknownCloudProviderError


def _create_nectar_connection(settings):
    region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
    connection = boto.connect_ec2(
        aws_access_key_id=settings['ec2_access_key'],
        aws_secret_access_key=settings['ec2_secret_key'],
        is_secure=True,
        region=region,
        port=8773,
        path="/services/Cloud")
    #logger.info("settings %s" % settings)
    logger.debug("Connecting to... %s" % region.name)
    return connection


def _create_csrack_connection(settings):
    logger.debug('Connecting to csrack')
    #region = RegionInfo(name="nova", endpoint="10.234.0.1")
    region = RegionInfo(name="nova", endpoint="131.170.250.250")
    connection = boto.connect_ec2(
        aws_access_key_id=settings['ec2_access_key'],
        aws_secret_access_key=settings['ec2_secret_key'],
        is_secure=False,
        region=region,
        port=8773,
        path="/services/Cloud")
    #logger.info("settings %s" % settings)
    logger.info("Connected to csrack")
    return connection


def _create_amazon_connection(settings):
    connection = boto.ec2.connect_to_region("ap-southeast-2", # connects to Sydney region
        aws_access_key_id=settings['ec2_access_key'],
        aws_secret_access_key=settings['ec2_secret_key'],
        is_secure=True,
        )
    return connection


def _does_vm_exist(vm):
    try:
        vm.update()
    except EC2ResponseError as e:
        if 'InstanceNotFound' in e.error_code:
            return False
    return True

#fixme consider using _does_vm_exist(vm)
def _is_vm_terminated(vm):
    """
        Checks whether an vm with @vm_id
        is running or not
    """
    try:
        vm.update()
        if vm.state in 'terminated':
            return True
    except EC2ResponseError as e:
        logger.debug('EC2ResponseError caught')
        if 'InstanceNotFound' in e.error_code \
            or 'InvalidInstanceID' in e.error_code:
            return True
        logger.debug('error not caught %s' % e.error_code)
        raise
    except Exception, e:
        logger.debug('EC2ResponseError NOT caught %s' % e)
        raise
    return False


def _get_all_vms(settings):
    connection = _create_cloud_connection(settings)
    reservations = connection.get_all_instances()
    res = {}
    all_vms = []
    logger.debug("reservations=%s" % reservations)
    for reservation in reservations:
        nodes = reservation.instances
        logger.debug("nodes=%s" % res)
        res[reservation] = nodes
        for i in nodes:
            all_vms.append(i)
    logger.debug("Nodes=%s" % res)
    return all_vms
