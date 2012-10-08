# Copyright (C) 2012, RMIT University

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

#import paramiko
import sys
import os
import time
import traceback
import logging
import hashlib

from libcloud.compute.types import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.providers import get_driver

#from sshconnector import *
from sshconnector import open_connection
from sshconnector import run_command
from sshconnector import is_ssh_ready


logger = logging.getLogger(__name__)
NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']


def _create_cloud_connection(settings):
    OpenstackDriver = get_driver(Provider.EUCALYPTUS)
    logger.debug("Connecting to... %s" % OpenstackDriver)
    connection = OpenstackDriver(settings['EC2_ACCESS_KEY'],
                                 secret=settings['EC2_SECRET_KEY'],
                                 host="nova.rc.nectar.org.au", secure=True,
                                 port=8773, path="/services/Cloud")
    logger.debug("Connected")
    return connection


def create_environ(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return id
    """
    logger.info("create_environ")
    all_instances = _create_VM_instances(number_vm_instances, settings)

    if all_instances:
        all_running_instances = _wait_for_instance_to_start_running(all_instances, settings)
        group_id = _store_md5_on_instances(all_running_instances, settings)
        print 'Created VM instances:'
        print_all_information(settings, all_instances=all_running_instances)
        return group_id

    return None


def _create_VM_instances(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return ip_address
    """
    connection = _create_cloud_connection(settings)
    images = connection.list_images()
    sizes = connection.list_sizes()
    image1 = [i for i in images if i.id == settings['VM_IMAGE']][0]
    size1 = [i for i in sizes if i.id == settings['VM_SIZE']][0]

    # TODO: make SSH security group here.
    all_instances = []
    try:
        print "Creating %d VM instance(s)" % number_vm_instances
        instance_count = 0
        while instance_count < number_vm_instances:
            new_instance = connection.create_node(name="New Centos VM instance",
                                                  size=size1, image=image1,
                                                  ex_keyname=settings['PRIVATE_KEY_NAME'],
                                                  ex_securitygroup=settings['SECURITY_GROUP'])
            all_instances.append(new_instance)
            instance_count += 1
    except Exception, e:
        if "QuotaError" in e[0]:
            print "Quota Limit Reached: "
            print "\t %s instances are created." % len(all_instances)
            print "\t Additional %s instances will not be created\
            " % (number_vm_instances - len(all_instances))
            print ' Running VM instances:'
            print_all_information(settings)
        else:
            traceback.print_exc(file=sys.stdout)

    return all_instances


def _store_md5_on_instances(all_instances, settings):
    group_id = _generate_group_id(all_instances)
    print "Creating group '%s' ..." % group_id
    for instance in all_instances:
        # login and check for md5 file
        instance_id = instance.name
        ip_address = get_instance_ip(instance_id, settings)
        ssh_ready = is_ssh_ready(settings, ip_address)
        if ssh_ready:
            print "Registering %s (%s) to group '%s'\
            " % (instance_id, ip_address, group_id)
            ssh = open_connection(ip_address=ip_address, settings=settings)
            group_id_path = os.path.join(settings['GROUP_ID_DIR'], group_id)
            run_command(ssh, "mkdir %s" % settings['GROUP_ID_DIR'])
            run_command(ssh, "touch %s" % group_id_path)
        else:
            print "VM instance %s will not be registered to group '%s'\
            " % (instance_id, ip, group_id)

    return group_id


def _generate_group_id(all_instances):
    md5_starter_string = ""
    for instance in all_instances:
        md5_starter_string += instance.name

    md5 = hashlib.md5()
    md5.update(md5_starter_string)
    group_id = md5.hexdigest()

    return group_id


def collect_instances(settings, group_id=None, instance_id=None, all_VM=False):
    connection = _create_cloud_connection(settings)
    all_instances = []
    if all_VM:
        all_instances = connection.list_nodes()
    elif group_id:
        all_instances = get_rego_nodes(group_id, settings)
    elif instance_id:
        if is_instance_running(instance_id, settings):
            all_instances.append(_get_this_instance(instance_id, settings))

    return all_instances


def confirm_teardown(settings, all_instances):
    print "Instances to be deleted are "
    print_all_information(settings, all_instances=all_instances)
    teardown_confirmation = None
    while not teardown_confirmation:
        teardown_confirmation = raw_input("Are you sure you want to delete (yes/no)? ")
        if teardown_confirmation != 'yes' and teardown_confirmation != 'no':
            teardown_confirmation = None

    if teardown_confirmation == 'yes':
        return True
    else:
        return False


def destroy_environ(settings, all_instances):
    """
        Terminate
            - all instances, or
            - a group of instances, or
            - a single instance
    """
    logger.info("destroy_environ")
    if not all_instances:
        logging.error("No running instance(s)")
        sys.exit(1)

    print "Terminating %d VM instance(s)" % len(all_instances)
    connection = _create_cloud_connection(settings)
    for instance in all_instances:
        try:
            connection.destroy_node(instance)
        except Exception:
            traceback.print_exc(file=sys.stdout)
    _wait_for_instance_to_terminate(all_instances, settings)


def is_instance_running(instance_id, settings):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance_running = False
    connection = _create_cloud_connection(settings)
    nodes = connection.list_nodes()
    for i in nodes:
        if i.name == instance_id and i.state == NodeState.RUNNING:
            instance_running = True
            break
    return instance_running


def _wait_for_instance_to_start_running(all_instances, settings):
    all_running_instances = []
    while all_instances:
        for instance in all_instances:
            instance_id = instance.name
            if is_instance_running(instance_id, settings):
                all_running_instances.append(instance)
                all_instances.remove(instance)
                print 'Current status of Instance %s: %s\
                ' % (instance_id, NODE_STATE[NodeState.RUNNING])
            else:
                print 'Current status of Instance %s: %s\
                ' % (instance_id, NODE_STATE[instance.state])

        time.sleep(settings['CLOUD_SLEEP_INTERVAL'])

    return all_running_instances


def _wait_for_instance_to_terminate(all_instances, settings):
    while all_instances:
        for instance in all_instances:
            instance_id = instance.name
            if not is_instance_running(instance_id, settings):
                all_instances.remove(instance)
                print 'Current status of Instance %s: %s\
                ' % (instance_id, NODE_STATE[NodeState.TERMINATED])
            else:
                print 'Current status of Instance %s: %s\
                ' % (instance_id, NODE_STATE[instance.state])

        time.sleep(settings['CLOUD_SLEEP_INTERVAL'])


def print_all_information(settings, all_instances=None):
    """
        Print information about running instances
            - ID
            - IP
            - VM type
            - list of groups
    """
    if not all_instances:
        connection = _create_cloud_connection(settings)
        all_instances = connection.list_nodes()
        if not all_instances:
            print '\t No running instances'
            sys.exit(1)

    counter = 1
    print '\tNo.\tID\t\tIP\t\tPackage\t\tGroup'
    for instance in all_instances:
        instance_id = instance.name
        ip = get_instance_ip(instance_id, settings)
        #if is_ssh_ready(settings, ip):
        ssh = open_connection(ip, settings)
        group_name = run_command(ssh, "ls %s " % settings['GROUP_ID_DIR'])
        vm_type = 'Other'
        res = run_command(ssh, "[ -d %s ] && echo 1\
        " % settings['GROUP_ID_DIR'])
        if '1\n' in res:
            vm_type = 'RMIT'

        if not group_name:
            group_name = '-'

        print '\t%d:\t%s\t%s\t%s\t\t%s\
        ' % (counter, instance_id, ip, vm_type, group_name)
        counter += 1


def _get_this_instance(instance_id, settings):
    """
        Get a reference to node with instance_id
    """
    connection = _create_cloud_connection(settings)
    nodes = connection.list_nodes()
    this_node = []
    for i in nodes:
        if i.name == instance_id:
            this_node = i
            break

    return this_node


def get_instance_ip(instance_id, settings):
    """
        Get the ip address of a node
    """
    #TODO: throw exception if can't find instance_id
    connection = _create_cloud_connection(settings)
    ip = ''
    while instance_id == '' or ip == '':
        nodes = connection.list_nodes()
        for i in nodes:
            if i.name == instance_id and len(i.public_ips) > 0:
                ip = i.public_ips[0]
                break
    return ip


#newly added methods from simplepackage
def get_rego_nodes(group_id, settings):
    """
    Returns nectar nodes that are currently packaged enabled.
    """
    logger.debug("get_rego_nodes")
    # get all available nodes
    conn = _create_cloud_connection(settings)
    packaged_node = []
    for node in conn.list_nodes():
        # login and check for md5 file
        ssh = open_connection(ip_address=get_instance_ip(node.name, settings),
                              settings=settings)
        # NOTE: assumes use of bash shell
        group_id_path = os.path.join(settings['GROUP_ID_DIR'], group_id)
        res = run_command(ssh, "[ -f %s ] && echo 1" % group_id_path)
        logger.debug("res=%s" % res)
        if '1\n' in res:
            logger.debug("node %s exists for group %s "
                         % (node.name, group_id))
            packaged_node.append(node)
        else:
            logger.debug("NO node for %s exists for group %s "
                         % (node.name, group_id))
    logger.debug("get_rego_nodes DONE")
    return packaged_node
