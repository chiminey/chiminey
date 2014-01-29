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

import sys
import boto
import time
import logging

from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError


logger = logging.getLogger(__name__)
NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']


def create_vms(total_vms, settings):
    """
        Create vms and return ip_address
    """
    # #fixme avoid hardcoding, move to settings.py
    # if settings['platform_type'] == 'csrack':
    #     placement = None
    #     vm_image = "ami-00000004"
    # elif settings['platform_type'] == 'nectar':
    #     placement = 'monash'
    #     vm_image = "ami-0000000d"
    # else:
    #     return []

    from django.conf import settings as django_settings

    try:
        platform_type = settings['platform_type']
        if platform_type in django_settings.VM_IMAGES:
            params = django_settings.VM_IMAGES[platform_type]
            placement = params['placement']
            vm_image = params['vm_image']
        else:
            return []
    except IndexError, e:
        logger.error("cannot load vm parameters")
        return []

    connection = _create_cloud_connection(settings)
    all_vms = []
    logger.info("Creating %d VM(s)" % total_vms)
    try:
        reservation = connection.run_instances(
                    placement=placement,
                    image_id=vm_image,
                    min_count=1,
                    max_count=total_vms,
                    key_name=settings['private_key_name'],
                    security_groups=[settings['security_group']],
                    instance_type=settings['vm_image_size'])
        logger.debug("Created Reservation %s" % reservation)
        for vm in reservation.instances:
            all_vms.append(vm)
    except EC2ResponseError as e:
        logger.error(e)
        logger.debug('error_code=%s' % e.error_code)
        logger.error(e.message)
        if 'TooManyInstances' not in e.error_code:
            logger.debug(e)
            raise
    logger.debug(all_vms)
    logger.debug('%d of %d requested VM(s) created'
                 % (len(all_vms), total_vms))
    return all_vms


def destroy_vms(settings, all_vms, ids_of_all_vms=None):
    """
        Terminate
            - all vms, or
            - a group of vms, or
            - a single vm
    """
    if not all_vms:
        logging.error("No running vm(s)")
        return

    if not ids_of_all_vms:
        ids_of_all_vms = []
        for vm in all_vms:
            ids_of_all_vms.append(vm.id)

    logger.info("Terminating %d vm(s)" % len(ids_of_all_vms))
    connection = _create_cloud_connection(settings)
    terminated_vms = connection.terminate_instances(ids_of_all_vms)
    return terminated_vms


def wait_for_vms_to_start_running(all_vms, settings):
    all_running_vms = []
    # FIXME: add final timeout for when VMs fail to initialise properly
    # TODO: spamming all nodes in tenancy continually is impolite, so should
    # store nodes we know to be part of this run (in context?)
    logger.debug("Started waiting")
    #maximum rwait time 3 minutes
    minutes = 3 #fixme avoid hard coding; move to settings.py
    max_retries = (minutes * 60)/settings['cloud_sleep_interval']
    retries = 0
    while all_vms:
        for vm in all_vms:
            ip_address = vm.ip_address
            if not ip_address:
                ip_address = vm.private_ip_address
            logger.debug("this vm %s" % vm)
            if _does_vm_exist(vm):
                if is_vm_running(vm):
                    all_running_vms.append(vm)
                    all_vms.remove(vm)
            else:
                all_vms.remove(vm)
            logger.debug('Current status of %s: %s' % (ip_address, vm.state))
            if vm.state in 'error' or retries == max_retries:
                all_vms.remove(vm)
        retries += 1
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
    try:
        reservation_list = connection.get_all_instances(
            instance_ids=[vm_id], filters=None)
        for i in reservation_list[0].instances:
            if i.id in vm_id:
                return i
    except Exception, e:
        logger.debug(e)
        raise


def get_vm_ip(vm_id, settings):
    ip_address = ''
    connection = _create_cloud_connection(settings)
    try:
        reservation_list = connection.get_all_instances(
            instance_ids=[vm_id], filters=None)
        for vm in reservation_list[0].instances:
            if vm.id is vm_id:
                ip_address = vm.ip_address
                if not ip_address:
                    ip_address = vm.private_ip_address
                break
        return ip_address
    except Exception, e:
        logger.debug(e)
        raise


def is_vm_running(vm):
    """
        Checks whether a vm with @vm_id
        is running or not
    """
    try:
        vm.update()
        if vm.state in 'running':
            return True
    except boto.exception.EC2ResponseError, e:
        logger.debug(e)
    return False


def get_running_vms(settings):
    all_vms = _get_all_vms(settings)
    running_vms = []
    for vm in all_vms:
        if is_vm_running(vm):
            running_vms.append(vm)
    return running_vms

import os
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
        sys.exit()  # FIXME: throw exception


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
    logger.info("Connecting to... %s" % region.name)
    return connection


def _create_csrack_connection(settings):
    logger.debug('Connecting to csrack')
    region = RegionInfo(name="nova", endpoint="10.234.0.1")
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
    pass


def _does_vm_exist(vm):
    try:
        vm.update()
    except boto.exception.EC2ResponseError as e:
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
    except boto.exception.EC2ResponseError as e:
        if 'InstanceNotFound' in e.error_code \
            or 'InvalidInstanceID' in e.error_code:
            return True
        raise
    return False


def _get_all_vms(settings):
    connection = _create_cloud_connection(settings)
    reservations = connection.get_all_instances()
    res = {}
    all_vms = []
    for reservation in reservations:
        nodes = reservation.instances
        res[reservation] = nodes
        for i in nodes:
            all_vms.append(i)
    logger.debug("Nodes=%s" % res)
    return all_vms