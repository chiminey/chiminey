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
import random
import logging


from chiminey.cloudconnection import botoconnector
from chiminey.cloudconnection.errors import NoRegisteredVMError,\
    CreatingVMFailedError, VMNotFoundError
from chiminey.sshconnection import open_connection


logger = logging.getLogger(__name__)

def create_vms(settings):
    """
        Create virtual machines and return id
    """
    logger.debug("create_vms")
    try:
        all_vms = botoconnector.create_vms(settings)
        if all_vms:
            all_running_vms = botoconnector.wait_for_vms_to_start_running(
                all_vms, settings)
            if all_running_vms:
                ssh_ready_vms = _get_ssh_ready_vms(
                    all_running_vms, settings)
                if ssh_ready_vms:
                    group_id = _generate_group_id(ssh_ready_vms)
                    return group_id, ssh_ready_vms
    except CreatingVMFailedError as e:
        logger.debug(e)
    return '', []


def get_registered_vms(settings, node_type='created_nodes'):
    res = []
    try:
        requested_nodes = settings[node_type]
        logger.debug('requested_nodes= %s' % requested_nodes)
        nodes = ast.literal_eval(requested_nodes)
        logger.debug('nodes= %s' % nodes)
        if nodes:
            for node in nodes:
                try:
                    vm = get_this_vm(node[0], settings)
                    res.append(vm)
                except VMNotFoundError as e:
                    logger.debug('vm [%s:%s] not found' % (node[0], node[1]))
                    logger.debug(e)
    except KeyError as e:
        logger.debug("settings=%s" % settings)
        logger.debug("node_type=%s" % node_type)
        logger.debug('key_error=%s' % e)
    except ValueError as e:
        logger.debug('value_error=%s' % e)
    logger.debug("nodes=%s" % res)
    if not res:
        raise NoRegisteredVMError
    return res


def destroy_vms(settings, node_types=['created_nodes'],
                registered_vms=[]):
    logger.info("destroy_vms")
    logger.debug('registered_vms=%s' % registered_vms)
    all_vms = registered_vms
    for type in node_types:
        logger.debug('type=%s' % type)
        try:
            all_vms.extend(get_registered_vms(
                settings, node_type=type))
        except NoRegisteredVMError as e:
            pass
    logger.debug('all_vms(teardown)=%s' % all_vms)
    terminated_vms = botoconnector.destroy_vms(
        settings, all_vms)
    botoconnector.wait_for_vms_to_terminate(
        terminated_vms, settings)


def print_vms(settings, all_vms=None):
    """
        Print information about running vms
            - ID
            - IP
            - VM type
            - list of groups
    """
    if not all_vms:
        all_vms = botoconnector.get_running_vms(settings)
        if not all_vms:
            logger.info('\t No running vms')
            return
    counter = 1
    logger.info('\tNo.\tID\t\tIP\t\tPackage\t\tGroup')
    for vm in all_vms:
        vm_id = vm.id
        ip = vm.ip_address
        if not ip:
            ip = vm.private_ip_address
        logger.info('\t%d:\t%s\t%s' % (counter, vm_id, ip))
        counter += 1


def is_vm_running(vm):
    return botoconnector.is_vm_running(vm)


def get_this_vm(vm_id, settings):
    return botoconnector.get_this_vm(vm_id, settings)


def get_vm_ip(vm_id, settings):
    return botoconnector.get_vm_ip(vm_id, settings)


def _get_ssh_ready_vms(all_vms, settings):
    '''
        Returns vms that can be reached via ssh
    '''
    ssh_ready_vms = []
    for vm in all_vms:
        ip = vm.ip_address
        if not ip:
            ip = vm.private_ip_address
        try:
            if _is_ssh_ready(settings, ip):
                ssh_ready_vms.append(vm)
                logger.debug('[%s] is ssh ready' % ip)
        except Exception as ex:
            logger.debug("[%s] Exception: %s" % (ip, ex))
        logger.debug('ssh ready vms are %s' % ssh_ready_vms)
    return ssh_ready_vms


def _is_ssh_ready(settings, ip_address):
    ssh_ready = False
    #maximum rwait time 3 minutes
    minutes = 3 #fixme avoid hard coding; move to settings.py
    max_retries = (minutes * 60)/settings['cloud_sleep_interval']
    retries = 0
    while not ssh_ready and retries < max_retries:
        logger.debug("Connecting to %s in progress ..." % ip_address)
        try:
            open_connection(ip_address, settings)
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


def _generate_group_id(all_vms):
    md5_starter_string = str(random.random())
    for vm in all_vms:
        md5_starter_string += vm.id
    md5 = hashlib.md5()
    md5.update(md5_starter_string)
    group_id = md5.hexdigest()
    return group_id
