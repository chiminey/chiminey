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

import logging

from chiminey.smartconnectorscheduler.errors import deprecated
from chiminey.sshconnection import open_connection
logger = logging.getLogger(__name__)


def run_command(command, ip_address, settings):
    ssh = open_connection(ip_address=ip_address, settings=settings)
    try:
        output, err = run_command_with_status(ssh, command)
    finally:
        ssh.close()
    return (output, err)


def run_command_with_status(ssh_client, command, current_dir=None, requiretty=False):

    """
    Provides an abstraction layer over the remote execution of an arbitrary
    shell command at the given target.

    :param ssh_client: the ssh_connector package handle.

    :param command: shell command to execute.

    :param current_dir: root_path to the location of the on the remote system. If None, uses the default path (home directory).

    :Return: tuple (out, err) containing command stdout and stderr, respectively.
    """
    # TODO: need a proper timeout for this command

    logger.debug("run_command %s; %s " % (current_dir, command))
    if current_dir:
        command = "cd %s;%s" % (current_dir, command)
    logger.debug(command)
    stderr = ""
    try:
        if requiretty:
            logger.debug("requiredttty")
            ssh_client.invoke_shell()
            stdin, stdout, stderr = ssh_client.exec_command(command)
            res = stdout.readlines()
            errs = stderr.readlines()
        else:
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


def run_make(ssh_client, makefile_path, target):
    """
    Provides an abstraction layer over the remote execution of a makefile
    command at the given target.

    :param ssh_client: the ssh_connector package handle.

    :param makefile_path: the location of the Makefile

    :param target: Makefile target to execute

    :Return: tuple (out, err) containing command stdout and stderr, respectively.
    """
    logger.debug("makefile_path=%s" % makefile_path)
    logger.debug("target=%s" % target)

    #command = "cd %s; make -f Makefile %s" % (makefile_path, target)
    command = "cd %s; sudo make -f Makefile %s" % (makefile_path, target)
    command_out = ''
    errs = ''
    try:
        command_out, errs = run_command_with_status(ssh_client, command)
        #command_out, errs = run_sudo_command_with_status(ssh_client, command)
    except Exception, e:
        logger.error("problem with runmake %s" % e)
    logger.debug("command_out2=(%s, %s)" % (command_out, errs))
    return (command_out, errs)


@deprecated
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


@deprecated
def run_sudo_command_with_status(ssh_client, command, settings):
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

@deprecated
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
