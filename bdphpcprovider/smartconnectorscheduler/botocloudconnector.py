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
    provider = settings['PROVIDER']
    if provider.lower() == "amazon" :
        return _create_amazon_connection(settings)
    elif provider.lower() == "nectar" :
        return _create_nectar_connection(settings)
    else:
        print "Unknown provider: %s" %provider
        sys.exit()#FIXME: throw exception


def _create_nectar_connection(settings):
    region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
    connection = boto.connect_ec2(
        aws_access_key_id=settings['EC2_ACCESS_KEY'],
        aws_secret_access_key=settings['EC2_SECRET_KEY'],
        is_secure=True,
        region=region,
        port=8773,
        path="/services/Cloud")

    logger.info("Connecting to... %s" % region.name)
    return connection


def _create_amazon_connection(settings):
    pass


def create_environ(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return id
    """
    logger.info("create_environ")
    all_instances =_create_VM_instances(number_vm_instances, settings)
    logger.debug("Printing ---- %s " % all_instances)


    if all_instances:
        all_running_instances = _wait_for_instance_to_start_running(all_instances, settings)
        group_id = _store_md5_on_instances(all_running_instances, settings)
        _customize_prompt(all_running_instances, settings)
        print "Group ID %s" % group_id
        print 'Created VM instances:'
        print_all_information(settings, all_instances=all_running_instances)
        return group_id


    return None


def _create_VM_instances(number_vm_instances, settings):
    """
        Create the Nectar VM instance and return ip_address
    """
    connection = _create_cloud_connection(settings)
    all_instances = []
    try:
        print "Creating %d VM instance(s)" % number_vm_instances
        instance_count = 0
        print instance_count
        while instance_count < number_vm_instances:
            print number_vm_instances
            reservation = connection.run_instances(
                image_id=settings['VM_IMAGE'],
                min_count=1,
                max_count=1,
                key_name=settings['PRIVATE_KEY_NAME'],
                security_groups=settings['SECURITY_GROUP'],
                instance_type=settings['VM_SIZE'])
            logger.debug("Created Reservation %s" % reservation)
            new_instance = reservation.instances[0]
            logger.debug("Created Instance %s" % new_instance)
            all_instances.append(new_instance)
            instance_count += 1
    except EC2ResponseError, e:
        logger.debug(e)

    if len(all_instances) < number_vm_instances:
        excess_instances = number_vm_instances \
                            - len(all_instances)
        logger.debug("Quota Exceeded")
        print "Quota Limit Reached: "
        print "\t %s instances are created." % len(all_instances)
        print "\t Additional %s instances will" \
              " not be created" % excess_instances
        if len(all_instances) == 0:
            print ' Running VM instances:'
            print_all_information(settings)
    return all_instances


def _store_md5_on_instances(all_instances, settings):
    group_id = _generate_group_id(all_instances)
    print "Creating group '%s' ..." % group_id
    for instance in all_instances:
        # login and store md5 file
        logger.debug("Instance ID  ...")
        instance_id = instance.id
        logger.debug("Instance ID %s" % instance_id)
        ip_address = get_instance_ip(instance_id, settings)
        logger.debug("Instance IP %s" % ip_address)
        ssh_ready = is_ssh_ready(settings, ip_address)
        if ssh_ready:
            print "Registering %s (%s) to group '%s'\
            " % (instance_id, ip_address, group_id)
            ssh_client = open_connection(ip_address=ip_address, settings=settings)
            group_id_path = os.path.join(settings['GROUP_ID_DIR'], group_id)

            run_command(ssh_client, "mkdir %s" % settings['GROUP_ID_DIR'])
            logger.debug("Group ID directory created")
            run_command(ssh_client, "touch %s" % group_id_path)
            logger.debug("Group ID file created")
        else:
            print "VM instance %s will not be registered to group '%s'\
            " % (instance_id, ip_address, group_id)

    return group_id


def _customize_prompt(all_instances, settings):
    for instance in all_instances:
        instance_id = instance.id
        ip_address = get_instance_ip(instance_id, settings)
        logger.info("Customizing command prompt")
        ssh_ready = is_ssh_ready(settings, ip_address)
        if ssh_ready:
            ssh_client = open_connection(ip_address=ip_address, settings=settings)
            command_bash = 'echo \'export PS1="%s"\' >> .bash_profile' % settings['CUSTOM_PROMPT']
            command_csh = 'echo \'setenv PS1 "%s"\' >> .cshrc' % settings['CUSTOM_PROMPT']
            command = 'cd ~; %s; %s' % (command_bash, command_csh)
            logger.debug("Command Prompt %s" % command)
            run_command(ssh_client, command)
            logger.debug("Customized prompt")
        else:
            print "Unable to customize command " \
                  "prompt for VM instance %s" \
            % (instance_id, ip_address)


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
    elif instance_id:
        if is_instance_running(instance_id, settings):
            all_instances.append(_get_this_instance(instance_id, settings))

    return all_instances


def get_ids_of_instances(instances):
    ids_of_instances = []
    for instance in instances:
        ids_of_instances.append(instance.id)
    return ids_of_instances


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


    print "Terminating %d VM instance(s)" % len(ids_of_all_instances)
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


def is_instance_running(instance_id, settings):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance_running = False
    all_instances =  get_all_instances(settings)
    for instance in all_instances:
        if instance.id == instance_id:
            logger.debug("Instance Found")
            if instance.state == "running":
                instance_running = True
                break
        else:
            logger.debug("Instance not found")
    return instance_running


def _wait_for_instance_to_start_running(all_instances, settings):
    all_running_instances = []
    # FIXME: add final timeout for when VMs fail to initialise properly
    logger.debug("Started waiting")
    while all_instances:
        for instance in all_instances:
            logger.debug("this instance %s" % instance)
            if is_instance_running(instance.id, settings):
                logger.debug("Instance running %s" % instance)
                all_running_instances.append(instance)
                all_instances.remove(instance)
            else:
                logger.debug("Instance not running %s" % instance)

            #print  'Current status of Instance %s: %s' %(instance_id, instance.state)

        time.sleep(settings['CLOUD_SLEEP_INTERVAL'])

    return all_running_instances


def _wait_for_instance_to_terminate(all_instances, settings):
    while all_instances:
        for instance in all_instances:
            instance_id = instance.id
            if not is_instance_running(instance_id, settings):
                all_instances.remove(instance)
                '''print 'Current status of Instance %s: %s\
                ' % (instance_id, NODE_STATE[NodeState.TERMINATED])
                '''
            print  'Current status of Instance %s: %s' %(instance_id, instance.state)

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
        all_instances = get_running_instances(settings)
        if not all_instances:
            print '\t No running instances'
            sys.exit(1)

    counter = 1
    print '\tNo.\tID\t\tIP\t\tPackage\t\tGroup'
    for instance in all_instances:
        instance_id = instance.id
        ip = get_instance_ip(instance_id, settings)
        #if is_ssh_ready(settings, ip):
        try:
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
    logger.debug("Reservation %s" % reservations)
    all_instances = []
    for reservation in reservations:
        nodes = reservation.instances
        logger.debug("Nodes %s" % nodes)
        for i in nodes:
            all_instances.append(i)
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
        logger.debug(len(all_instances))
        if is_instance_running(instance.id, settings):
            running_instances.append(instance)
    return running_instances


#newly added methods from simplepackage
def get_rego_nodes(group_id, settings):
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
        logger.debug("ssh client created %s" % ssh_client)
        # NOTE: assumes use of bash shell
        group_id_path = os.path.join(settings['GROUP_ID_DIR'], group_id)
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
