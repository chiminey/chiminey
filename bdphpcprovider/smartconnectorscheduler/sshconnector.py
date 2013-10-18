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

from time import sleep
import paramiko
import os
import logging

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class AuthError(Error):
    pass


def is_ssh_ready(settings, ip_address):
    ssh_ready = False
    while not ssh_ready:
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
                pass
            sleep(settings['cloud_sleep_interval'])
    logger.debug("Connecting to %s completed" % ip_address)
    # TODO: need way of exiting polling loop if vm connection is borked.
    return ssh_ready


def open_connection(ip_address, settings):
    """
    Creates a ssh_client connection to the SSH at ip_address using
    credentials in settings
    """
    # open up the connection
    ssh_client = paramiko.SSHClient()
    # autoaccess new keys
    # Cloud instances are continually reused so ip address likely
    # be reused
    logger.debug('ssh_client=%s' % ssh_client)
    #TODO: check for existence of all settings values before going further.
    known_hosts_file = os.path.join("~", ".ssh", "known_hosts")
    ssh_client.load_system_host_keys(os.path.expanduser(known_hosts_file))
    #ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    #TODO: handle exceptions if connection does not work.
    # use private key if exists
    try:
        if 'private_key' in settings and 'username' in settings:
            if os.path.exists(settings['private_key']):
                logger.debug("Connecting as %s with key %s" % (settings['username'], settings['private_key']))
                private_key_file = settings['private_key']
                #privatekeyfile = os.path.expanduser(settings['private_key'])
                #logger.debug("privatekeyfile=%s" % private_key_file)
                mykey = paramiko.RSAKey.from_private_key_file(private_key_file)
                ssh_client.connect(ip_address, username=settings['username'],
                                   timeout=60.0, pkey=mykey)
        elif 'password' in settings and 'username' in settings:
            logger.debug("Connecting to %s as %s" % (ip_address,
                                settings['username']))
            print(ssh_client)
            ssh_client.connect(ip_address, username=settings['username'],
                               password=settings['password'], timeout=60.0)
        else:
            raise KeyError
    except paramiko.AuthenticationException, e:
        logger.debug(e)
        raise AuthError(e)
    except Exception, e:
        logger.error("[%s] Exception: %s" % (ip_address, e))
        raise
    logger.debug("Made connection")
    return ssh_client


def run_command(ssh_client, command, current_dir=None):
    """
    Given a ssh_client, execute command from the current_dir
    on the remote host and return stdout
    """
    # TODO: need a proper timeout for this command

    logger.debug("run_command %s; %s " % (current_dir, command))
    if current_dir:
        command = "cd %s;%s" % (current_dir, command)
    logger.debug(command)
    stdin, stdout, stderr = ssh_client.exec_command(command)
    res = stdout.readlines()
    logger.debug("run_command_stdout=%s" % res)
    if stderr:
        logger.error("run_command_stderr=%s" % stderr.readlines())
    return res


def run_command_with_status(ssh_client, command, current_dir=None):
    """
    Given a ssh_client, execute command from the current_dir
    on the remote host and return stdout and stderr
    """
    # TODO: need a proper timeout for this command

    logger.debug("run_command %s; %s " % (current_dir, command))
    if current_dir:
        command = "cd %s;%s" % (current_dir, command)
    logger.debug(command)

    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        res = stdout.readlines()
        errs = stderr.readlines()
    except Exception, e:
        logger.error(e)
        errs = [str(e)]
        res = []
    logger.debug("run_command_stdout=%s" % res)
    if stderr:
        logger.debug("run_command_stderr=%s" % stderr.readlines())
    return (res, errs)


def run_command_with_tty(ssh_client, command, settings, current_dir=None):
    """
        runs a command on remote server, but also creates a pseudotty which is
        required if sudo command will be executed at any point on the remote server
    """
    # TODO: need a proper timeout for this command

    chan = ssh_client.invoke_shell()
    logger.debug("Channel %s" % chan)
    #chan.send('sudo -s\n')
    logger.debug("Sending through channel %s" % chan)
    full_buff = ''
    buff = ''
    command_prompt = settings['custom_prompt']

    # while not command_prompt in buff:
    #     resp = chan.recv(9999)
    #     print resp
    #     buff += resp
    # logger.debug("buff = %s" % buff)
    # full_buff += buff

    chan.send("%s\n" % command)
    logger.debug("Command %s" % command)
    buff = ''

    #FIXME: need to include timeouts on all these recv calls
    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.send("echo $!\n")  # NOTE: we assume bash
    logger.debug("Command %s" % command)
    buff = ''

    #FIXME: need to include timeouts on all these recv calls
    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    error_code = buff
    full_buff += buff

    # TODO: handle stderr

    # chan.send("exit\n")
    # buff = ''

    # # FIXME: need to include timeouts on all these recv calls
    # while not command_prompt in buff:
    #     resp = chan.recv(9999)
    #     print resp
    #     buff += resp
    # logger.debug("buff = %s" % buff)
    # full_buff += buff

    chan.close()
    return (error_code, full_buff, '')




def run_sudo_command_with_status(ssh_client, command, settings, instance_id):
    """
    Runs command at the ssh_client remote but also returns error code
    """
    # TODO: need a proper timeout for this command
    chan = ssh_client.invoke_shell()
    logger.debug("Channel %s" % chan)
    chan.send('sudo -s\n')
    logger.debug("Sending through channel %s" % chan)
    full_buff = ''
    buff = ''
    command_prompt = settings['custom_prompt']

    #FIXME: need to include timeouts on all these recv calls
    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    logger.debug("Command %s" % command)
    buff = ''

    #FIXME: need to include timeouts on all these recv calls
    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.send("echo $!\n") # NOTE: we assume bash
    logger.debug("Command %s" % command)
    buff = ''

    #FIXME: need to include timeouts on all these recv calls
    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    error_code = buff
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''

    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.close()
    return (error_code, full_buff, '')


def run_sudo_command(ssh_client, command, settings, instance_id):
    chan = ssh_client.invoke_shell()
    logger.debug("Channel %s" % chan)
    chan.send('sudo -s\n')
    logger.debug("Sending through channel %s" % chan)
    full_buff = ''
    buff = ''
    command_prompt = settings['custom_prompt']

    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    logger.debug("Command %s" % command)
    buff = ''

    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''

    while not command_prompt in buff:
        resp = chan.recv(9999)
        print resp
        buff += resp
    logger.debug("buff = %s" % buff)
    full_buff += buff

    chan.close()
    return (full_buff, '')


# def run_sudo_command(self, ssh_client, command, settings, instance_id):
#     _, res = self.run_sudo_command_with_status(ssh_client, command, settings, instance_id)
#     return res

def install_deps(ssh_client, packages, settings, instance_id):
    for pack in packages:
        logger.debug("Setup %s" % pack)
        stdout, stderr = run_sudo_command(
            ssh_client, 'yum -y install %s' % pack,
            settings=settings, instance_id=instance_id)
        logger.debug("install stdout=%s" % stdout)
        logger.debug("install stderr=%s" % stderr)


def unpack(ssh_client, environ_dir, package_file):
    res = run_command(
        ssh_client, 'tar --directory=%s --extract --gunzip --verbose --file=%s'
        % (environ_dir, os.path.join(environ_dir, package_file)))
    logger.debug(res)


def unzip(ssh_client, zipped_file, destination_dir):
    res = run_command(
        ssh_client, 'unzip -o %s -d %s'
                    % (zipped_file, destination_dir))
    logger.debug(res)


def compile(ssh_client, environ_dir, compile_file,
            package_dirname, compiler_command):
    run_command(ssh_client,
                "%s %s.f -o %s " % (compiler_command,
                                    compile_file, compile_file),
                current_dir=os.path.join(environ_dir, package_dirname))


def mkdir(ssh_client, dir):
    run_command(ssh_client, "mkdir -p %s" % dir)


def find_remote_files(ssh, remote_dir, type='f'):
    command = "find %s -name \"*\" -type %s" % (remote_dir, type)
    res = run_command(ssh, command)
    files = []
    for f in res:
        files.append(f.rstrip())
    return files


def get_file(ssh_client, source_path, package_file, environ_dir):
    ftp = ssh_client.open_sftp()
    logger.debug("source=%s file=%s dest=%s"
                 % (source_path, package_file, environ_dir))
    source_file = os.path.join(source_path, package_file).replace('\\', '/')
    dest_file = os.path.join(environ_dir, package_file).replace('\\', '/')
    logger.debug("sfile=%s dfile=%s" % (source_file, dest_file))
    try:
        ftp.get(source_file, dest_file)
    except IOError as e:
        logger.warning("%s not found:%s" % (package_file, e))


def put_file(ssh_client, source_path, package_file, environ_dir):
    ftp = ssh_client.open_sftp()
    print "sftp connection opened"
    logger.debug("%s %s" % (source_path, environ_dir))
    source_file = os.path.join(source_path, package_file).replace('\\', '/')
    print "source %s" % source_file
    dest_file = os.path.join(environ_dir, package_file).replace('\\', '/')
    print "destination %s" % dest_file

    logger.debug("%s %s" % (source_file, dest_file))
    logger.debug("Source file %s, destination %s" % (source_file, dest_file))
    print ("Source file %s, destination %s" % (source_file, dest_file))
    ftp.put(source_file, dest_file)


# see /bdphpcprovider/smartconnectorscheduler/hrmcstages.py:439 - done
def put_payload(ssh_client, source, destination):
    ftp = ssh_client.open_sftp()
    logger.debug("Transferring payload from %s to %s" % (source, destination))

    for root, dirs, files in os.walk(source):
        prefix = root
        break

    for root, dirs, files in os.walk(source):
        relative_root = root[len(prefix) + 1:]
        if dirs:
            for dir in dirs:
                mkdir(ssh_client, os.path.join(destination,
                    relative_root, dir))
        if files:
            for file in files:
                try:
                    ftp.remove(os.path.join(destination, relative_root, file))
                except IOError:
                    logger.warn("File not found, and thus not be removed")
                ftp.put(os.path.join(root, file), os.path.join(destination,
                    relative_root, file))
    #TODO Check close statement in paramiko


def get_package_pids(ssh_client, command):
    #FIXME: the output of pidof is not entirely clear.,
    logger.debug("get_package_pids")
    pid_lines = run_command(ssh_client, "/sbin/pidof %s" % command)
    logger.debug("pid_lines=%s" % pid_lines)
    # could return multiple lines so pick first.
    pids = ""
    try:
        pids = pid_lines[0]
    except IndexError:
        pids = ""
    # if len(pid_lines) > 1:
    #     pids = pid_lines[0]  # if some returns, the pids are in first element
    # else:
    #     pids = pid_lines
    logger.debug("pids=%s" % pids)
    return pids.split(' ')
