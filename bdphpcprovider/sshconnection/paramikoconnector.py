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


import os
import paramiko
import logging

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class AuthError(Error):
    pass


def open_connection(ip_address, settings):
    """
    Creates a ssh_client connection to the SSH at ip_address using
    credentials in settings
    """
    # open up the connection
    ssh_client = paramiko.SSHClient()
    logger.debug('ssh_client=%s' % ssh_client)
    known_hosts_file = os.path.join("~", ".ssh", "known_hosts")
    ssh_client.load_system_host_keys(os.path.expanduser(known_hosts_file))
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
    # use private key if exists
    try:
        if 'private_key' in settings and 'username' in settings:
            if os.path.exists(settings['private_key']):
                logger.debug("Connecting as %s with key %s" % (settings['username'], settings['private_key']))
                private_key_file = settings['private_key']
                mykey = paramiko.RSAKey.from_private_key_file(private_key_file)
                ssh_client.connect(ip_address, username=settings['username'],
                                   timeout=60.0, pkey=mykey)
                logger.debug('private_keyfile_=%s' % private_key_file)
            else:
                raise IOError
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
