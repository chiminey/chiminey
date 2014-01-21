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

import time
import ast
import hashlib
import logging
from collections import namedtuple

from bdphpcprovider.cloudconnection import botoconnector
from bdphpcprovider.smartconnectorscheduler import sshconnector

logger = logging.getLogger(__name__)

def create_vms(total_vms, settings):
    """
        Create the Nectar VM instance and return id
    """
    logger.info("create_vms")
    all_instances = botoconnector.create_vm_instances(total_vms, settings)
    if all_instances:
        all_running_instances = botoconnector.wait_for_instance_to_start_running(
            all_instances, settings)
        if all_running_instances:
            ssh_ready_vms = _get_ssh_ready_instances(
                all_running_instances, settings)
            if ssh_ready_vms:
                group_id = _generate_group_id(ssh_ready_vms)
                return (group_id, ssh_ready_vms)
    return ('', [])


def destroy_vms(settings, all_instances, ids_of_all_instances=None):

    logger.info("destroy_vms")
    logger.debug('all_instances(teardown)=%s' % all_instances)
    terminated_instances = botoconnector.destroy_vm_instances(
        settings, all_instances,
        ids_of_all_instances=ids_of_all_instances)
    botoconnector.wait_for_instance_to_terminate(
        terminated_instances, settings)


def get_registered_vms(settings, node_type='created_nodes'):
    res = []
    try:
        requested_nodes = settings[node_type]
    except KeyError:
        logger.debug("settings=%s" % settings)
        logger.error("%s missing from context" % node_type)
        raise
    try:
        nodes = ast.literal_eval(requested_nodes)
    except KeyError:
        logger.error("error with parsing created_nodes")
        raise
    for node in nodes:
        instance = botoconnector.get_this_instance(node[0], settings)
        if not instance:
            logger.debug('instance [%s:%s] not found' % (node[0], node[1]))
        else:
            res.append(instance)
    logger.debug("nodes=%s" % res)
    return res


def print_vms(settings, all_instances=None):
    """
        Print information about running instances
            - ID
            - IP
            - VM type
            - list of groups
    """
    if not all_instances:
        all_instances = botoconnector.get_running_instances(settings)
        if not all_instances:
            logger.info('\t No running instances')
            return

    counter = 1
    logger.info('\tNo.\tID\t\tIP\t\tPackage\t\tGroup')
    for instance in all_instances:
        instance_id = instance.id
        ip = instance.ip_address
        if not ip:
            ip = instance.private_ip_address
        logger.info('\t%d:\t%s\t%s' % (counter, instance_id, ip))
        counter += 1


def is_instance_running(instance):
    return botoconnector.is_instance_running(instance)


def get_this_instance(instance_id, settings):
    return botoconnector.get_this_instance(instance_id, settings)


def _get_ssh_ready_instances(all_instances, settings):
    '''
        Returns instances that can be reached via ssh
    '''
    ssh_ready_instances = []
    for instance in all_instances:
        ip = instance.ip_address
        if not ip:
            ip = instance.private_ip_address
        try:
            if _is_ssh_ready(settings, ip):
                ssh_ready_instances.append(instance)
                logger.debug('[%s] is ssh ready' % ip)
        except Exception as ex:
            logger.debug("[%s] Exception: %s" % (ip, ex))
        logger.debug('ssh ready instances are %s' % ssh_ready_instances)
    return ssh_ready_instances


def _is_ssh_ready(settings, ip_address):
    ssh_ready = False
    #maximum rwait time 3 minutes
    minutes = 3 #fixme avoid hard coding; move to settings.py
    max_retries = (minutes * 60)/settings['cloud_sleep_interval']
    retries = 0
    while not ssh_ready and retries < max_retries:
        logger.debug("Connecting to %s in progress ..." % ip_address)
        try:
            sshconnector.open_connection(ip_address, settings)
            ssh_ready = True
        except Exception as ex:
            logger.debug("[%s] Exception: %s" % (ip_address, ex))
            if 'Connection refused' in ex:
                # FIXME: this doesn't always work.
                pass
            elif 'Authentication failed' in ex:
                pass
            else:
                retries += 1
            time.sleep(settings['cloud_sleep_interval'])
    logger.debug("Connecting to %s completed" % ip_address)
    return ssh_ready


def _generate_group_id(all_instances):
    md5_starter_string = ""
    for instance in all_instances:
        md5_starter_string += instance.id
    md5 = hashlib.md5()
    md5.update(md5_starter_string)
    group_id = md5.hexdigest()
    return group_id