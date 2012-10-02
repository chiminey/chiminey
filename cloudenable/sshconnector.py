from time import sleep

import paramiko
import os
import sys
import traceback
import logging

logger = logging.getLogger(__name__)

def is_ssh_ready(settings, ip_address):
    ssh_ready = False
    while not ssh_ready:
        try:
            ssh = open_connection(ip_address, settings)
            ssh_ready = True
        except Exception, e:
            sleep(settings['CLOUD_SLEEP_INTERVAL'])
            #print ("Connecting to %s in progress ..." % ip_address)
            #traceback.print_exc(file=sys.stdout)
    return ssh_ready

    
def open_connection(ip_address, settings):
    # open up the connection
    ssh = paramiko.SSHClient()
    # autoaccess new keys
    ssh.load_system_host_keys(os.path.expanduser(os.path.join("~",
                                                              ".ssh",
                                                              "known_hosts")))
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    #TODO: handle exceptions if connection does not work.
    # use private key if exists
    if os.path.exists(settings['PRIVATE_KEY']):
        privatekeyfile = os.path.expanduser(settings['PRIVATE_KEY'])
        mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        ssh.connect(ip_address, username=settings['USER_NAME'], timeout=60, pkey=mykey)
    else:
        print("%s %s %s" % (ip_address, settings['USER_NAME'], settings['PASSWORD']))
        print(ssh)
        ssh.connect(ip_address, username=settings['USER_NAME'],
                    password=settings['PASSWORD'], timeout=60)

    #channel = ssh.invoke_shell().open_session()
    return ssh


def run_command(ssh, command, current_dir=None):
    logger.debug("%s %s " % (current_dir, command))
    if current_dir:
        command = "cd %s;%s" % (current_dir, command)
    logger.debug(command)
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.readlines()


def _run_sudo_command(ssh, command, settings, instance_id):

    chan = ssh.invoke_shell()
    chan.send('sudo -s\n')
    full_buff = ''
    buff = ''
    buff_size = 9999
    while not '[%s@%s ~]$ ' % (settings['USER_NAME'], instance_id) in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
    #print("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    buff = ''
    while not '[root@%s %s]# ' % (instance_id, settings['USER_NAME']) in buff:
        resp = chan.recv(buff_size)
        print(resp)
        buff += resp
    #print("buff = %s" % buff)
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''
    while not '[%s@%s ~]$ ' % (settings['USER_NAME'], instance_id) in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
   # print("3buff = %s" % buff)
    full_buff += buff

    chan.close()
    print full_buff
    return (full_buff, '')
