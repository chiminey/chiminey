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

import sys
import boto
import os
import time
import logging
import hashlib

import ast
from collections import namedtuple


from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
from bdphpcprovider.smartconnectorscheduler.sshconnector import open_connection,\
    run_command, is_ssh_ready, AuthError

logger = logging.getLogger(__name__)
NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']


'''
class Fake_VM:
    id = "115.146.92.233"
    public_ips = ["115.146.92.233"]
    state = 0 # Equivalent to RUNNING
    def __init__(self):
        pass
'''


def _create_cloud_connection(settings):
    provider = settings['platform']
    if provider.lower() == "amazon":
        return _create_amazon_connection(settings)
    elif provider.lower() == "nectar":
        return _create_nectar_connection(settings)
    else:
        logger.info("Unknown provider: %s" % provider)
        sys.exit()  # FIXME: throw exception


def _create_nectar_connection(settings):
    region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
    connection = boto.connect_ec2(
        aws_access_key_id=settings['nectar_ec2_access_key'],
        aws_secret_access_key=settings['nectar_ec2_secret_key'],
        is_secure=True,
        region=region,
        port=8773,
        path="/services/Cloud")
    #logger.info("settings %s" % settings)
    logger.info("Connecting to... %s" % region.name)
    return connection


def _create_amazon_connection(settings):
    pass


def create_environ(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return id
    """
    logger.info("create_environ")
    all_instances = create_VM_instances(number_vm_instances, settings)
    if all_instances:
        all_running_instances = _wait_for_instance_to_start_running(all_instances, settings)

        #logger.info('Created VM instances:')
        #print_all_information(settings, all_instances=all_running_instances)
        #nodes = retrieve_node_info(group_id,
        #    settings)
        return all_running_instances
        # FIXME: if host keys check fail, then need to remove offending
        # key from known_hosts and try again.
    return None


def create_VM_instances(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return ip_address
    """
    # TODO: create the required security group settings (e.g., ssh) at
    # nectar automagically, so we can control allowed ports etc.
    connection = _create_cloud_connection(settings)
    all_instances = []
    try:
        logger.info("Creating %d VM instance(s)" % number_vm_instances)
        instance_count = 0
        logger.debug("Instance Count %d total %d" % (instance_count,
            number_vm_instances))
        while instance_count < number_vm_instances:
            #logger.debug(number_vm_instances)
            reservation = connection.run_instances(
                placement='monash',
                image_id=settings['vm_image'],
                min_count=1,
                max_count=1,
                key_name=settings['nectar_private_key_name'],
                security_groups=settings['security_group'],
                instance_type=settings['vm_size'])
            logger.debug("Created Reservation %s" % reservation)
            new_instance = reservation.instances[0]
            logger.debug("Created Instance %s" % new_instance)
            all_instances.append(new_instance)
            instance_count += 1
    except EC2ResponseError, e:
        logger.debug("Reservation not created")
        logger.debug(e)

    if len(all_instances) < number_vm_instances:
        excess_instances = number_vm_instances \
                            - len(all_instances)
        logger.debug("Quota Exceeded")
        logger.info("Quota Limit Reached: ")
        logger.info("\t %s instances are created." % len(all_instances))
        logger.info("\t Additional %s instances will" \
              " not be created" % excess_instances)
        if len(all_instances) == 0:
            logger.info('Running VM instances:')
            print_all_information(settings)
    return all_instances


def get_ssh_ready_instances(all_instances, settings):
    '''
        Returns instances that can be reached via ssh
    '''
    ssh_ready_instances = []
    for instance in all_instances:
        ip = instance.ip_address
        try:
            if is_ssh_ready(settings, ip):
                ssh_ready_instances.append(instance)
                logger.debug('[%s] is ssh ready' % ip)
        except Exception as ex:
            logger.debug("[%s] Exception: %s" % (instance.ip_address, ex))
    return ssh_ready_instances


def brand_instances(all_instances, settings):
    group_id = _generate_group_id(all_instances)
    branded_instances = []
    if all_instances:
        branded_instances = _store_md5_on_instances(all_instances,
                                                    group_id, settings)
        branded_instances = _customize_prompt(branded_instances, settings)
    return (group_id, branded_instances)


def _store_md5_on_instances(all_instances, group_id, settings):
    logger.info("Creating vm group '%s' ..." % group_id)
    instances_with_groupid = []
    for instance in all_instances:
        # login and store md5 file
        ip_address = instance.ip_address
        logger.debug("Instance IP %s" % ip_address)
        try:
            logger.info("Registering %s to group '%s'\
            " % (ip_address, group_id))
            ssh_client = open_connection(ip_address=ip_address, settings=settings)
            group_id_path = os.path.join(settings['group_id_dir'], group_id)
            run_command(ssh_client, "mkdir %s" % settings['group_id_dir'])
            logger.info("Group ID directory created")
            run_command(ssh_client, "touch %s" % group_id_path)
            logger.info("Group ID file created")
            instances_with_groupid.append(instance)
        except Exception as ex:
            logger.info("VM instance %s will not be registered to group '%s'\
            " % (ip_address, group_id))
            logger.deug(ex)
    return instances_with_groupid


def _customize_prompt(all_instances, settings):
    cusstomised_instances = []
    for instance in all_instances:
        ip_address = instance.ip_address
        logger.info("Customizing command prompt")
        logger.debug("Custom prompt %s" % settings['custom_prompt'])
        try:
            ssh_client = open_connection(ip_address=ip_address, settings=settings)
            command_bash = 'echo \'export PS1="%s"\' >> .bash_profile' % settings['custom_prompt']
            command_csh = 'echo \'setenv PS1 "%s"\' >> .cshrc' % settings['custom_prompt']
            command = 'cd ~; %s; %s' % (command_bash, command_csh)
            logger.debug("Command Prompt %s" % command)
            run_command(ssh_client, command)
            logger.debug("Customized prompt")
            cusstomised_instances(instance)
        except Exception as ex:
            logger.info("Unable to customize command " \
                  "prompt for VM instance %s" \
            % (ip_address))
            logger.debug(ex)
    return cusstomised_instances


def _generate_group_id(all_instances):
    md5_starter_string = ""
    for instance in all_instances:
        md5_starter_string += instance.id
    md5 = hashlib.md5()
    md5.update(md5_starter_string)
    group_id = md5.hexdigest()
    return group_id


def collect_instances(settings, group_id=None, instance_id=None, all_VM=False):
    all_instances = []
    if all_VM:
        all_instances = get_running_instances(settings)
    elif group_id:
        all_instances = get_rego_nodes(group_id, settings)

#    elif instance_id:
#        if is_instance_running(instance_id, settings):
#            all_instances.append(_get_this_instance(instance_id, settings))
    return all_instances


def get_ids_of_instances(instances):
    ids_of_instances = []
    for instance in instances:
        ids_of_instances.append(instance.id)
    return ids_of_instances


def confirm_teardown(settings, all_instances):
    logger.info("Instances to be deleted are ")
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


def destroy_environ(settings, all_instances, ids_of_all_instances=None):
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

    if not ids_of_all_instances:
        ids_of_all_instances = []
        for instance in all_instances:
            ids_of_all_instances.append(instance.id)

    logger.info("Terminating %d VM instance(s)" % len(ids_of_all_instances))
    connection = _create_cloud_connection(settings)
    connection.terminate_instances(ids_of_all_instances)

    '''
    for instance in all_instances:
        try:

            connection.destroy_node(instance)
        except Exception:
            traceback.print_exc(file=sys.stdout)
    '''
    _wait_for_instance_to_terminate(all_instances, settings)


def is_instance_running(instance):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance.update()
    if instance.state in 'running':
        return True
    return False


def _wait_for_instance_to_start_running(all_instances, settings):
    all_running_instances = []
    # FIXME: add final timeout for when VMs fail to initialise properly
    # TODO: spamming all nodes in tenancy continually is impolite, so should
    # store nodes we know to be part of this run (in context?)
    logger.debug("Started waiting")
    while all_instances:
        for instance in all_instances:
            logger.debug("this instance %s" % instance)
            if is_instance_running(instance):
                logger.debug("Instance running %s" % instance)
                all_running_instances.append(instance)
                all_instances.remove(instance)
            else:
                logger.debug("Instance not running %s" % instance)
            logger.debug('Current status of Instance %s: %s' % (instance, instance.state))
        time.sleep(settings['cloud_sleep_interval'])
    return all_running_instances


def is_instance_terminated(instance):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance.update()
    if instance.state in 'terminated':
        return True
    return False


def _wait_for_instance_to_terminate(all_instances, settings):
    while all_instances:
        for instance in all_instances:
            if is_instance_terminated(instance):
                all_instances.remove(instance)
                logger.debug('Instance %s terminated' % instance.ip_address)
        time.sleep(settings['cloud_sleep_interval'])


def print_all_information(settings, all_instances=None):
    """
        Print information about running instances
            - ID
            - IP
            - VM type
            - list of groups
    """
    if not all_instances:
        all_instances = get_running_instances(settings)
        if not all_instances:
            logger.info('\t No running instances')
            sys.exit(1)

    counter = 1
    logger.info('\tNo.\tID\t\tIP\t\tPackage\t\tGroup')
    for instance in all_instances:
        instance_id = instance.id
        ip = get_instance_ip(instance_id, settings)
        #if is_ssh_ready(settings, ip):
        try:
            ssh = open_connection(ip, settings)
            group_name = run_command(ssh, "ls %s " % settings['group_id_dir'])
            vm_type = 'Other'
            res = run_command(ssh, "[ -d %s ] && echo 1\
            " % settings['group_id_dir'])

            if '1\n' in res:
                vm_type = 'RMIT'

            if not group_name:
                group_name = '-'

            logger.info('\t%d:\t%s\t%s\t%s\t\t%s\
            ' % (counter, instance_id, ip, vm_type, group_name))
            counter += 1
        except AuthError:
            logger.debug("Trying to access VMs that "
                         "are not created with the provided private key")



def _get_this_instance(instance_id, settings):
    """
        Get a reference to node with instance_id
    """
    nodes = get_all_instances(settings)
    this_node = []
    for i in nodes:
        if i.id == instance_id:
            this_node = i
            break
    return this_node


def get_all_instances(settings):
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


def get_instance_ip(instance_id, settings):
    """
        Get the ip address of an instance
    """
    #TODO: throw exception if can't find instance_id
    all_instances =  get_all_instances(settings)
    ip_address = ''
    for instance in all_instances:
        if instance.id == instance_id:
            ip_address = instance.ip_address
            logger.debug("IP %s", ip_address)
            break
    return ip_address


def get_running_instances(settings):
    all_instances = get_all_instances(settings)
    running_instances = []
    for instance in all_instances:
        #logger.debug(len(all_instances))
        if is_instance_running(instance):
            running_instances.append(instance)
    return running_instances


def get_rego_nodes(group_id, settings):

    res = []
    NodeInfo = namedtuple('NodeInfo',
        ['id', 'ip'])
    try:
        created_nodes = settings['created_nodes']
    except KeyError:
        logger.debug("settings=%s" % settings)
        logger.error("created_nodes missing from context")
        raise
    try:
        nodes = ast.literal_eval(created_nodes)
    except KeyError:
        logger.error("error with parsing created_nodes")
        raise
    for node in nodes:
        res.append(NodeInfo(id=node[0], ip=node[1]))
    logger.debug("nodes=%s" % res)
    return res


def retrieve_node_info(group_id, settings):
    """
    Returns nectar nodes that are currently packaged enabled.
    """
    logger.debug("get_rego_nodes")
    # get all available nodes
    packaged_node = []
    running_instances = get_running_instances(settings)
    for node in running_instances:
        # login and check for md5 file
        instance_id = node.id
        ip = get_instance_ip(instance_id, settings)
        try:
            ssh_client = open_connection(ip_address=ip,
                              settings=settings)
        except AuthError:
            logger.warn("node skipped as cannot access")
            continue
        except Exception, e:
            # TODO: we assume crashed nodes not in group, we
            # need to store the assigned IPs in the context
            # to avoid having to recheck all nodes.
            logger.error("get_rego_nodes exception %s" % e)
            continue
        logger.debug("ssh client created %s" % ssh_client)
        # NOTE: assumes use of bash shell
        group_id_path = os.path.join(settings['group_id_dir'], group_id)
        res = run_command(ssh_client, "[ -f %s ] && echo 1" % group_id_path)
        logger.debug("res=%s" % res)
        if '1\n' in res:
            logger.debug("node %s exists for group %s "
                         % (instance_id, group_id))
            packaged_node.append(node)
        else:
            logger.debug("NO node for %s exists for group %s "
                         % (instance_id, group_id))
    logger.debug("get_rego_nodes DONE")
    return packaged_node
