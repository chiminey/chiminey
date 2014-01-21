# Copyright (C) 2013, RMIT University

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

# Contains the specific connectors and stages for HRMC

import os
import logging
import time
import getpass
import paramiko

from pprint import pformat
from urlparse import urlparse, parse_qsl
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from storages.backends.sftpstorage import SFTPStorage
from paramiko.ssh_exception import SSHException

from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError

logger = logging.getLogger(__name__)


def get_bdp_root_path():
    bdp_root_path = '/var/cloudenabling/remotesys'  # fixme avoid hard coding; systematically determine bdp_root_path
    return bdp_root_path


class RemoteStorage(SFTPStorage):
    def __init__(self, settings=None):
        import pkg_resources
        version = pkg_resources.get_distribution("django_storages").version
        if not version == "1.1.8":
            logger.warn("ConnectorStorage overrides version 1.1.8 of django_storages. found version %s" % version)

        super(RemoteStorage, self).__init__()
        if 'params' in settings:
            super(RemoteStorage, self).__dict__["_params"] = settings['params']
        if 'root' in settings:
            super(RemoteStorage, self).__dict__["_root_path"] = settings['root']
        if 'host' in settings:
            super(RemoteStorage, self).__dict__["_host"] = settings['host']
        super(RemoteStorage, self).__dict__["_dir_mode"] = 0700
        print super(RemoteStorage, self)

    def _connect(self):
        """ Overrides internal behaviour to not store host keys
            Warning: may stop working for later version of SFTPStorage
            FIXME: this approach is brittle for later version of SFTPStorage
        """
        self._ssh = paramiko.SSHClient()

        if self._known_host_file is not None:
            self._ssh.load_host_keys(self._known_host_file)
        else:
            # warn BUT DONT ADD host keys from current user.
            self._ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

        # and automatically add new host keys for hosts we haven't seen before.
        self._ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

        try:
            self._ssh.connect(self._host, **self._params)
        except paramiko.AuthenticationException, e:
            if self._interactive and 'password' not in self._params:
                # If authentication has failed, and we haven't already tried
                # username/password, and configuration allows it, then try
                # again with username/password.
                if 'username' not in self._params:
                    self._params['username'] = getpass.getuser()
                self._params['password'] = getpass.getpass()
                self._connect()
            else:
                raise paramiko.AuthenticationException, e

        if not hasattr(self, '_sftp'):
            self._sftp = self._ssh.open_sftp()

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        if self.exists(name):
            self.delete(name)
        return name


class LocalStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        super(LocalStorage, self).__init__(location, base_url)

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        if self.exists(name):
            self.delete(name)
        return name


def get_value(key, dictionary):
    """
    Return the value for the key in the dictionary, or a blank
    string
    """
    try:
        return dictionary[key]
    except KeyError, e:
        logger.debug(e)
        return u''


def get_http_url(non_http_url):
    curr_scheme = non_http_url.split(':')[0]
    http_url = "http" + non_http_url[len(curr_scheme):]
    return http_url


def parse_bdpurl(bdp_url):
    """
    Break down a BDP url into component parts via http protocol and urlparse
    """
    scheme = urlparse(bdp_url).scheme
    http_file_url = get_http_url(bdp_url)
    o = urlparse(http_file_url)
    mypath = o.path
    location = o.netloc
    host = o.hostname
    if mypath[0] == os.path.sep:
        mypath = mypath[1:]
    logger.debug("mypath=%s" % mypath)
    query = parse_qsl(o.query)
    query_settings = dict(x[0:] for x in query)
    logger.debug('bdp_url=%s' % bdp_url)
    logger.debug('query_settings=%s' % query_settings)
    return (scheme, host, mypath, location, query_settings)


def get_remote_path(bdp_url):
    """
    Get the actual path for the bdp_url
    """
    logger.debug("bdp_url=%s" % bdp_url)
    (scheme, host, mypath, location, query_setting) = parse_bdpurl(bdp_url)
    root_path = query_setting['root_path']
    remote_path = os.path.join(root_path, mypath)
    logger.debug("remote_path=%s" % remote_path)
    return remote_path


def delete_files(url, exceptions=None):
    """
    Supports only file and ssh schemes
    :param url:
    :param exceptions:
    :return:
    """
    logger.debug("delete_files")
    # http_url = get_http_url(url)
    # path = urlparse(http_url).path
    # if path[0] == os.path.sep:
    #     path = path[1:]
    (scheme, host, path, location, query_settings) = parse_bdpurl(url)
    logger.debug('Path %s ' % path)

    fsys = get_filesystem(url)
    logger.debug("fsys=%s" % pformat(fsys))
    try:
        current_content = fsys.listdir(path)
    except Exception, e:
        logger.warn("cannot get content %s" % e)
        current_content = []
    logger.debug("current_content=%s" % pformat(current_content))
    current_path_pointer = path
    file_path_holder = []
    dir_path_holder = []
    while len(current_content) > 0:
        logger.debug("Current Content %s " % pformat(current_content))
        for fname in current_content[1]:
            logger.debug("fname=%s" % fname)
            if fname in exceptions:
                logger.debug("not deleting %s" % fname)
                continue
            file_path = str(os.path.join(current_path_pointer, fname))
            logger.debug("file_path=%s" % file_path)
            file_path_holder.append(file_path)
            # FIXME: detect permission/existnce of file_path
            fsys.delete(file_path)
            logger.debug('filepath=%s deleted' % file_path)
            #content = fs.open(file_path).read()
            #updated_file_path = file_path[len(source_path)+1:]
            #curr_dest_url = os.path.join(destination_prefix, updated_file_path) \
            #                + destination_suffix
            #logger.debug("Current destination url %s" % curr_dest_url)
            #put_file(curr_dest_url, content)
        for dirname in current_content[0]:
            abs_dirname = [os.path.join(current_path_pointer, dirname), True]
            dir_path_holder.append(abs_dirname)

        current_content = []
        for k in dir_path_holder:
            if k[1]:
                k[1] = False
                current_path_pointer = k[0]
                current_content = fsys.listdir(current_path_pointer)
                logger.debug("Current pointer %s " % current_path_pointer)
                break


def list_dirs(url, list_files=False):
    logger.debug("url=%s" % url)
    http_url = get_http_url(url)
    logger.debug("http_url=%s", http_url)
    logger.debug("list_files=%s", list_files)
    path = urlparse(http_url).path
    if path[0] == os.path.sep:
        path = path[1:]
    logger.debug('Path %s ' % path)
    fsys = get_filesystem(url)

    if list_files:
        l = fsys.listdir(path)[1]
    else:
        l = fsys.listdir(path)[0]

    logger.debug("Directory (File) list %s" % l)
    return l


def get_filesystem(bdp_url):
    """
    """
    # scheme = urlparse(url).scheme
    # http_url = get_http_url(url)
    # parsed_url = urlparse(http_url)
    # query = parse_qsl(parsed_url.query)
    # query_settings = dict(x[0:] for x in query)
    (scheme, host, mpath, location, query_settings) = parse_bdpurl(bdp_url)
    logger.debug("mpath=%s" % mpath)
    if scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
    elif scheme == "ssh":
        logger.debug("getting from ssh")
        key_file = get_value('key_file', query_settings)
        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file
        ssh_settings = {'params': paramiko_settings,
                        'host': host,
                        'root': str(root_path) + "/"}
        logger.debug("nci_settings=%s" % pformat(ssh_settings))
        fs = RemoteStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % scheme)
        return
    return fs


def list_all_files(source_url):
    """
    Supports only file and ssh schemes
    :param source_url:
    :return:
    """
    """
    # FIXME: will not copy individual files

    source_scheme = urlparse(source_url).scheme
    logger.debug("source_scheme=%s" % source_scheme)
    http_source_url = get_http_url(source_url)
    logger.debug("http_source_url=%s" % http_source_url)
    source = urlparse(http_source_url)
    source_location = source.netloc
    logger.debug("source_location=%s" % source_location)
    source_path = source.path
    logger.debug("source_path=%s" % source_path)
    query = parse_qsl(source.query)
    query_settings = dict(x[0:] for x in query)

    if source_path[0] == os.path.sep:
        source_path = source_path[1:]

    """
    logger.debug("list_all_files")
    (source_scheme, source_location, source_path, source_location, query_settings) = parse_bdpurl(source_url)


    if source_scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
    elif source_scheme == "ssh":
        logger.debug("getting from ssh")
        key_file = get_value('key_file', query_settings)
        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file
        ssh_settings = {'params': paramiko_settings,
                        'host': source_location,
                        'root': str(root_path) + "/"}
        logger.debug("nci_settings=%s" % pformat(ssh_settings))
        fs = RemoteStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % source_scheme)
        return

    logger.debug("source_path=%s"  % source_path)

    if fs.exists(source_path):
        logger.debug("source_path exists")
        current_content = fs.listdir(source_path)
    else:
        return []
    #logger.debug("current_content=%s" % current_content)
    current_path_pointer = source_path
    dir_path_holder = []
    file_paths = []
    while len(current_content) > 0:
        for i in current_content[1]:
            file_path = str(os.path.join(current_path_pointer, i))
            file_paths.append(file_path)
        for j in current_content[0]:
            list = [os.path.join(current_path_pointer, j), True]
            dir_path_holder.append(list)
        current_content = []
        for k in dir_path_holder:
            if k[1]:
                k[1] = False
                current_path_pointer = k[0]
                current_content = fs.listdir(current_path_pointer)
                logger.debug("Current pointer %s " % current_path_pointer)
                break

    return sorted(file_paths)


def copy_directories(source_url, destination_url):
    """
    Supports only file and ssh schemes
    :param source_url:
    :param destination_url:
    :return:
    """
    # FIXME: Will not work with individual files, only directories
    # TODO: replace with parse_bdpurl()
    logger.debug("copy_directories %s -> %s" % (source_url, destination_url))

    (source_scheme, host, source_path,
        source_location, query_settings) = parse_bdpurl(source_url)

    http_source_url = get_http_url(source_url)
    source_prefix = source_url.split('?')[0]
    logger.debug("source_prefix=%s" % source_prefix)
    source = urlparse(http_source_url)
    source_query = source.query

    if source_query:
        source_suffix = "?" + source_url.split('?')[1]
    else:
        source_suffix = ""
    logger.debug("source_suffix=%s" % source_suffix)

    http_destination_url = get_http_url(destination_url)
    destination_prefix = destination_url.split('?')[0]
    logger.debug("destination_prefix=%s" % destination_prefix)

    destination = urlparse(http_destination_url)
    destination_query = destination.query

    if destination_query:
        destination_suffix = "?" + destination_url.split('?')[1]
    else:
        destination_suffix = ""
    logger.debug("destination_suffix=%s" % destination_suffix)

    # TODO: replace with call to get_filesystem
    if source_scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
    elif source_scheme == "ssh":
        logger.debug("getting from ssh")
        key_file = get_value('key_file', query_settings)
        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file
        ssh_settings = {'params': paramiko_settings,
                        'host': source_location,
                        'root': str(root_path) + "/"}
        logger.debug("nci_settings=%s" % pformat(ssh_settings))
        fs = RemoteStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % source_scheme)
        return

    if source_path:
        if source_path[0] == os.path.sep:
            source_path = source_path[1:]
        if source_path[-1] == os.path.sep:
            source_path = source_path[:-1]
    logger.debug("source_path=%s" % source_path)

    dir_file_info = fs.listdir(source_path)
    if dir_file_info:
        logger.debug("dir_file_info=%s" % pformat(dir_file_info))
    current_dirname = source_path
    logger.debug("current_dirname=%s" % current_dirname)
    file_paths = []
    dir_paths = []
    while len(dir_file_info) > 0:
        # for each file in current directory
        for fname in dir_file_info[1]:
            logger.debug("fname=%s" % fname)
            file_path = str(os.path.join(current_dirname, fname))
            #if file_path[0] != os.path.sep:
            #    file_path = "/%s" % file_path
            logger.debug("file_path=%s" % file_path)
            file_paths.append(file_path)
            logger.debug("file_paths=%s" % file_paths)
            updated_file_path = file_path[len(source_path) + 1:]
            logger.debug("updated_file_path=%s" % updated_file_path)

            curr_source_url = os.path.join(source_prefix, updated_file_path) \
                + source_suffix
            logger.debug("Current source url %s" % curr_source_url)

            fail = False
            delay = 1
            #fixme move to ftmanager
            for i in xrange(1, 10):
                try:
                    content = get_file(curr_source_url)
                except SSHException, e:
                    logger.error(e)
                    fail = True
                except Exception, e:
                    logger.error(e)
                    fail = True
                else:
                    fail = False
                if not fail:
                    break
                logger.warn("problem with getfile, sleeping %s" % delay)
                time.sleep(delay)
                delay += delay
            if fail:
                raise e

            # FIXME: file_path is a relative path from fs.  Is that compabible with myTardis?
            #content = fs.open(file_path).read()  # Can't we just call get_file ?
            logger.debug("content loaded")
            curr_dest_url = os.path.join(destination_prefix, updated_file_path) \
                            + destination_suffix
            logger.debug("Current destination url %s" % curr_dest_url)
            put_file(curr_dest_url, content)
        # for each directory below current directory
        for directory in dir_file_info[0]:
            logger.debug("directory=%s" % directory)
            list = [os.path.join(current_dirname, directory), True]
            logger.debug("list=%s" % list)
            dir_paths.append(list)
            logger.debug("dir_paths=%s" % dir_paths)

        dir_file_info = []
        for k in dir_paths:
            if k[1]:
                k[1] = False
                current_dirname = k[0]
                dir_file_info = fs.listdir(current_dirname)
                logger.debug("Current pointer %s " % current_dirname)
                break
    logger.debug("All files")
    logger.debug(file_paths)
    logger.debug(dir_paths)
    logger.debug("end of copy_directories")


def put_file(file_url, content):
    """
    Writes out the content to the file_url using config info from user_settings. Note that content is bytecodes
    """
    logger.debug("file_url=%s" % file_url)
    #logger.debug('content=%s' % content)
    if '..' in file_url:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")
    scheme = urlparse(file_url).scheme
    http_file_url = get_http_url(file_url)
    # TODO: replace with parse_bdp_url()
    o = urlparse(http_file_url)
    mypath = o.path
    location = o.netloc
    if mypath[0] == os.path.sep:
        mypath = mypath[1:]
    logger.debug("mypath=%s" % mypath)
    query = parse_qsl(o.query)
    query_settings = dict(x[0:] for x in query)

    if '@' in location:
        location = location.split('@')[1]

    if scheme == 'http':
        # TODO: test
        import urllib
        import urllib2
        values = {'name': 'Michael Foord',
          'location': 'Northampton',
          'language': 'Python'}
        data = urllib.urlencode(values)
        req = urllib2.Request(file_url, data)
        response = urllib2.urlopen(req)
        res = response.read()
        logger.debug("response=%s" % res)
    elif scheme == "ssh":
        key_file = get_value('key_file', query_settings)
        if not key_file:
            key_file = None  # require None for ssh_settings to skip keys
        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("key_file=%s" % key_file)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file
        ssh_settings = {'params': paramiko_settings,
                        'host': location,
                        'root': str(root_path) + "/"}
        logger.debug("ssh_settings=%s" % ssh_settings)
        fs = RemoteStorage(settings=ssh_settings)
         # FIXME: does this overwrite?
        fs.save(mypath, ContentFile(content))  # NB: ContentFile only takes bytes
        logger.debug("File to be written on %s" % location)
    elif scheme == "tardis":
        # TODO: do a POST of a new datafile into existing exp and dataset
        # parse file_url to extract tardis host, exp_id and dataset_id
        from bdphpcprovider.mytardis import create_datafile
        create_datafile(file_url, content)
    elif scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("remote_fs_path=%s" % root_path)
        fs = LocalStorage(location=root_path)
        dest_path = fs.save(mypath, ContentFile(content))  # NB: ContentFile only takes bytes
        logger.debug("dest_path=%s" % dest_path)
    return content


def dir_exists(dir_url):
    # Can't use exists here because directories cannot be accessed directly
    # FIXME: this can be slow
    logger.debug("dir_url=%s" % dir_url)
    try:
        file_paths = list_all_files(dir_url)
    except OSError:
        return False
    logger.debug("file_paths=%s" % pformat(file_paths))
    return len(file_paths) > 0


def file_exists(bdp_file_url):
    logger.debug("bdp_file_url=%s" % bdp_file_url)
    (source_scheme, source_location, source_path, source_location, query_settings) = parse_bdpurl(bdp_file_url)
    if source_scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
    elif source_scheme == "ssh":
        logger.debug("getting from ssh")
        key_file = get_value('key_file', query_settings)
        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file
        ssh_settings = {'params': paramiko_settings,
                        'host': source_location,
                        'root': str(root_path) + "/"}
        logger.debug("nci_settings=%s" % pformat(ssh_settings))
        fs = RemoteStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % source_scheme)
        return

    logger.debug("source_path=%s" % source_path)

    return fs.exists(source_path)


def get_file(file_url):
    """
    Reads in content at file_url using config info from user_settings
    Returns byte strings
    """
    fp = get_filep(file_url)
    content = fp.read()

    if content and (len(content) > 100):
        logger.debug("content(abbrev)=\n%s\n ... \n%s\nEOF\n" % (content[:100], content[-100:]))
    else:
        logger.debug("content=%s" % content)
    return content


def get_filep(file_bdp_url, sftp_reference=False):
    """
    opens a django file pointer to file_bdp_url
    """
    logger.debug("file_bdp_url=%s" % file_bdp_url)
    if '..' in file_bdp_url:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")

    # scheme = urlparse(file_bdp_url).scheme
    # http_file_url = get_http_url(file_bdp_url)
    # o = urlparse(http_file_url)
    # mypath = str(o.path)
    # location = o.netloc
    (scheme, host, mypath, location, query_settings) = parse_bdpurl(file_bdp_url)
    logger.debug("scheme=%s" % scheme)
    logger.debug("mypath=%s" % mypath)
    #if mypath[0] == os.path.sep:
    #    mypath = str(mypath[1:])
    #logger.debug("mypath=%s" % mypath)
    # query = parse_qsl(o.query)
    # query_settings = dict(x[0:] for x in query)

    if '@' in location:
        location = location.split('@')[1]

    if scheme == 'http':
        import urllib2
        req = urllib2.Request(o)
        fp = urllib2.urlopen(req)

        #content = response.read()
    elif scheme == "ssh":
        logger.debug("getting from hpc")
        key_file = get_value('key_file', query_settings)
        logger.debug('key_file=%s' % key_file)
        if not key_file:
            key_file = None  # require None for ssh_settinglesss to skip keys

        username = get_value('username', query_settings)
        password = get_value('password', query_settings)
        root_path = get_value('root_path', query_settings)
        logger.debug("root_path=%s" % root_path)
        paramiko_settings = {'username': username,
            'password': password}
        if key_file:
            paramiko_settings['key_filename'] = key_file

        ssh_settings = {'params': paramiko_settings,
                        'host': location,
                        'root': root_path + "/"}
        logger.debug("ssh_settings=%s" % ssh_settings)
        fs = RemoteStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
        logger.debug("mypath=%s" % mypath)
        fp = fs.open(mypath)
        logger.debug("fp opened")
        logger.debug("fp_dict %s" % fp.__dict__)
        #content = fp.read()
        #logger.debug("content=%s" % content)
    elif scheme == "tardis":
        # TODO: implement GET of a datafile in a given exp and dataset
        # parse file_bdp_url to extract tardis host, exp_id and dataset_id
        exp_id = 0
        dataset_id = 0
        from bdphpcprovider.mytardis import retrieve_datafile
        retrieve_datafile(file_bdp_url, exp_id, dataset_id)
        # TODO: get content and make a file pointer out of it
        return "a={{a}} b={{b}}"
        raise NotImplementedError("tardis scheme not implemented")
    elif scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
        fp = fs.open(mypath)
        #content = fs.open(mypath).read()
        #logger.debug("content=%s" % content)
    if sftp_reference:
        return fp, fs
    return fp

