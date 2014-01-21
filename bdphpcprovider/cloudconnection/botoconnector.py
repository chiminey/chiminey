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


def create_vm_instances(total_vms, settings):
    """
        Create the Nectar VM instance and return ip_address
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
    all_instances = []
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
        for instance in reservation.instances:
            all_instances.append(instance)
    except EC2ResponseError as e:
        logger.error(e)
        logger.debug('error_code=%s' % e.error_code)
        logger.error(e.message)
        if 'TooManyInstances' not in e.error_code:
            logger.debug(e)
            raise
    logger.debug(all_instances)
    logger.debug('%d of %d requested VM(s) created'
                 % (len(all_instances), total_vms))
    return all_instances


def destroy_vm_instances(settings, all_instances, ids_of_all_instances=None):
    """
        Terminate
            - all instances, or
            - a group of instances, or
            - a single instance
    """
    if not all_instances:
        logging.error("No running instance(s)")
        return

    if not ids_of_all_instances:
        ids_of_all_instances = []
        for instance in all_instances:
            ids_of_all_instances.append(instance.id)

    logger.info("Terminating %d VM instance(s)" % len(ids_of_all_instances))
    connection = _create_cloud_connection(settings)
    terminated_instances = connection.terminate_instances(ids_of_all_instances)
    return terminated_instances


def wait_for_instance_to_start_running(all_instances, settings):
    all_running_instances = []
    # FIXME: add final timeout for when VMs fail to initialise properly
    # TODO: spamming all nodes in tenancy continually is impolite, so should
    # store nodes we know to be part of this run (in context?)
    logger.debug("Started waiting")
    #maximum rwait time 3 minutes
    minutes = 3 #fixme avoid hard coding; move to settings.py
    max_retries = (minutes * 60)/settings['cloud_sleep_interval']
    retries = 0
    while all_instances:
        for instance in all_instances:
            ip_address = instance.ip_address
            if not ip_address:
                ip_address = instance.private_ip_address
            logger.debug("this instance %s" % instance)
            if _does_instance_exist(instance):
                if is_instance_running(instance):
                    all_running_instances.append(instance)
                    all_instances.remove(instance)
            else:
                all_instances.remove(instance)
            logger.debug('Current status of %s: %s' % (ip_address, instance.state))
            if instance.state in 'error' or retries == max_retries:
                all_instances.remove(instance)
        retries += 1
        time.sleep(settings['cloud_sleep_interval'])
    return all_running_instances


def wait_for_instance_to_terminate(all_instances, settings):
    logger.debug('remaining_instances=%s' % all_instances)
    while all_instances:
        for instance in all_instances:
            current_instance = instance
            ip_address = instance.ip_address
            if not ip_address:
                ip_address = instance.private_ip_address
            if _is_instance_terminated(current_instance):
                all_instances.remove(instance)
                logger.debug('Current status of %s: %s' % (ip_address, 'terminated'))
                logger.debug('remaining_instances=%s' % all_instances)
            else:
                logger.debug('Current status of %s: %s' % (ip_address, instance.state))
        time.sleep(settings['cloud_sleep_interval'])


def get_this_instance(instance_id, settings):
    connection = _create_cloud_connection(settings)
    try:
        reservation_list = connection.get_all_instances(
            instance_ids=[instance_id], filters=None)
        for i in reservation_list[0].instances:
            if i.id in instance_id:
                return i
    except Exception, e:
        logger.debug(e)


def is_instance_running(instance):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    try:
        instance.update()
        if instance.state in 'running':
            return True
    except boto.exception.EC2ResponseError, e:
        logger.debug(e)
    return False


def get_running_instances(settings):
    all_instances = _get_all_instances(settings)
    running_instances = []
    for instance in all_instances:
        if is_instance_running(instance):
            running_instances.append(instance)
    return running_instances


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


def _does_instance_exist(instance):
    try:
        instance.update()
    except boto.exception.EC2ResponseError as e:
        if 'InstanceNotFound' in e.error_code:
            return False
    return True

#fixme consider using _does_instance_exist(instance)
def _is_instance_terminated(instance):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    try:
        instance.update()
        if instance.state in 'terminated':
            return True
    except boto.exception.EC2ResponseError as e:
        if 'InstanceNotFound' in e.error_code \
            or 'InvalidInstanceID' in e.error_code:
            return True
        raise
    return False


def _get_all_instances(settings):
    connection = _create_cloud_connection(settings)
    reservations = connection.get_all_instances()
    res = {}
    #logger.debug("Reservation instances %s" % reservations)
    all_instances = []
    for reservation in reservations:
        nodes = reservation.instances
        res[reservation] = nodes
        for i in nodes:
            all_instances.append(i)
    logger.debug("Nodes=%s" % res)
    return all_instances