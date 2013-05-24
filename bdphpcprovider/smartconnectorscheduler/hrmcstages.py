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
import logging.config
import json
import collections
from pprint import pformat
import paramiko
import getpass
from urlparse import urlparse, parse_qsl

from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from storages.backends.sftpstorage import SFTPStorage

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI, SmartConnector, get_url_with_pkey
from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, \
    collect_instances, destroy_environ
from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing, InvalidInputError
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import deprecated

logger = logging.getLogger(__name__)


@deprecated
def get_filesys(context):
    """
    Return the filesys in the context
    """
    try:
        val = context['filesys']
    except KeyError:
        message = 'Context missing "filesys" key'
        logger.exception(message)
        raise ContextKeyMissing(message)
    return val


@deprecated
def _load_file(fsys, fname):
    """
    Returns the dataobject for fname in fsys, or empty data object if error
    """
    try:
        config = fsys.retrieve(fname)
    except KeyError, e:
        config = DataObject(fname, '')
        logger.warn("Cannot load %s %s" % (fname, e))
    return config


def retrieve_settings(profile):
    """
    Using the user_id in the context, retrieves all the settings files from the profile models
    """
    settings = {}
    for param in models.UserProfileParameter.objects.filter(paramset__user_profile=profile):
        logger.debug("param=%s" % param)
        try:
            settings[param.name.name] = param.getValue()
        except Exception:
            logger.error("Invalid settings values found for %s" % param)
            raise BadInputException()
        logger.debug("%s %s %s" % (param.paramset.schema, param.name,
            param.getValue()))

    return settings

@deprecated
def get_file_from_context(context, fname):
    """
    Retrieve the content of a remote file with fname
    """
    fsys_path = context['fsys']
    remote_fs = FileSystemStorage(location=fsys_path)
    f = context[fname]
    content = remote_fs.open(f).read()
    return content

@deprecated
def get_settings(context):
    """
    Return contents of config.sys file as a dictionary
    """
    try:
        fsys = get_filesys(context)
        #logger.debug("fsys= %s" % fsys)
        fname = "default/config.sys"
        config = _load_file(fsys, fname)
        #logger.debug("config= %s" % config)
        settings_text = config.retrieve()
        #logger.debug("settings_text= %s" % settings_text)
        settings = dict(json.loads(settings_text))
        return settings
    except ContextKeyMissing:
        logger.debug('ContextKeyMissing exception')
        raise

@deprecated
def _get_run_info_file(context):
    """
    Returns the actual runinfo data object. If problem, return blank data object
    """
    fsys = get_filesys(context)
    #logger.debug("fsys= %s" % fsys)
    config = _load_file(fsys, "default/runinfo.sys")
    #logger.debug("config= %s" % config)
    return config


@deprecated
def get_run_info(context):
    """
    Returns the content of the run info as file a dict. If problem, return {}
    """
    try:
        get_filesys(context)
    except ContextKeyMissing:
        return {}
    #logger.debug("fsys= %s" % fsys)
    config = _get_run_info_file(context)
    #logger.debug("config= %s" % config)
    if config:
        settings_text = config.retrieve()
        #logger.debug("runinfo_text= %s" % settings_text)
        res = json.loads(settings_text)
        #logger.debug("res=%s" % dict(res))
        return dict(res)
    return {}


@deprecated
def get_all_settings(context):
    """
    Returns a single dict containing content of config.sys and runinfo.sys
    """
    settings = get_settings(context)
    run_info = get_run_info(context)
    settings.update(run_info)
    settings.update(context)
    return settings


@deprecated
def update_key(key, value, context):
    """
    Updates key from the filesystem runinfo.sys file to a new values
    """
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = _load_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    logger.debug("removing %s" % key)
    settings[key] = value  # FIXME: possible race condition?
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)

@deprecated
def delete_key(key, context):
    """
    Removes key from the filesystem runinfo.sys file
    """
    filesystem = get_filesys(context)
    logger.debug("filesystem= %s" % filesystem)

    run_info_file = _load_file(filesystem, "default/runinfo.sys")
    logger.debug("run_info_file= %s" % run_info_file)

    run_info_file_content = run_info_file.retrieve()
    logger.debug("runinfo_content= %s" % run_info_file_content)

    settings = json.loads(run_info_file_content)
    del settings[key]
    logger.debug("configuration=%s" % settings)

    run_info_content_blob = json.dumps(settings)
    run_info_file.setContent(run_info_content_blob)
    filesystem.update("default", run_info_file)


def get_fanout(parameter_value_list):
    '''
    total_fanout = 1
    if len(self.threshold) > 1:
        for i in self.threshold:
            total_fanout *= self.threshold[i]
    else:
        total_picks = self.threshold[0]
    '''
    pass


def get_threshold():
    pass


def safe_import(path, args, kw):
    """
        Dynamically imports a package at path and executes it current namespace with given args
    """

    logger.debug("path %s args %s kw %s  " % (path, args, kw))
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a filter module' % path)
    filter_module, filter_classname = path[:dot], path[dot + 1:]
    try:
        mod = import_module(filter_module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing filter %s: "%s"' %
                                   (filter_module, e))
    try:
        filter_class = getattr(mod, filter_classname)
    except AttributeError:
        raise ImproperlyConfigured('Filter module "%s" does not define a "%s" class' %
                                   (filter_module, filter_classname))

    filter_instance = filter_class(*args, **kw)
    return filter_instance


def values_match_schema(schema, values):
    """
        Given a schema object and a set of (k,v) fields, checking
        each k has correspondingly named ParameterName in the schema
    """
    # TODO:
    return True


def get_new_local_url(url):
    """
    Create local resource to hold instantiated template for command execution.

    """

    # # The top of the remote filesystem that will hold a user's files
    remote_base_path = os.path.join("centos")

    o = urlparse(url)
    file_path = o.path.decode('utf-8')
    logger.debug("file_path=%s" % file_path)
    # if file_path[0] == os.path.sep:
    #     file_path = file_path[:-1]
    import uuid
    randsuffix = unicode(uuid.uuid4())  # should use some job id here

    relpath = u"%s_%s" % (file_path, randsuffix)

    if relpath[0] == os.path.sep:
        relpath = relpath[1:]
    logger.debug("relpath=%s" % relpath)

    # FIXME: for django storage, do we need to create
    # intermediate directories
    dest_path = os.path.join(remote_base_path, relpath)
    logger.debug("dest_path=%s" % dest_path)
    return u'file://%s' % dest_path.decode('utf8')


def _get_command_actual_args(directive_args, user_settings):
    """
    Parse the directive args to make command args
    """
    command_args = []
    for darg in directive_args:
        logger.debug("darg=%s" % darg)
        rendering_context = {}
        metadatas = darg[1:]
        file_url = darg[0].decode('utf8')

        if metadatas:
            # make rendering_context based on metadata key value pairs
            for metadata in metadatas:
                logger.debug("metadata=%s" % metadata)
                # parse configuration parameters
                if metadata:  # if we have [] as argument
                    sch = metadata[0].decode('utf8')
                    # FIXME: error handling
                    try:
                        metadata_schema = models.Schema.objects.get(namespace=sch)
                    except models.Schema.DoesNotExist:
                        msg = "schema %s does not exist choices are " % sch
                        msg += ",".join([x.namespace for x in models.Schema.objects.all()])
                        logger.exception(msg)
                        raise
                    variables = metadata[1:]
                    logger.debug("variables=%s" % variables)
                    if not values_match_schema(metadata_schema, variables):
                        raise InvalidInputError(
                            "specified parameters do not match schema")
                    for k, v in variables:
                        # FIXME: need way of specifying ns and name in the template
                        # to distinuish between different templates. Here all the variables
                        # across entire template file must be disjoint. Custom
                        # tag may do it.
                        if not k:
                            raise InvalidInputError(
                                "Cannot have blank key in parameter set")
                        # FIXME: handle all different tytpes
                        try:
                            typed_val = int(v)
                        except ValueError:
                           typed_val = v.decode('utf8')  # as a string
                        except TypeError:
                            typed_val = ""

                        if file_url:
                            rendering_context[k.decode('utf8')] = typed_val
                        else:
                            command_args.append((("%s/%s" % (metadata_schema.namespace, k))
                                .decode('utf8'), typed_val))

        # retrieve the file url and resolve against rendering_context
        if file_url:
            # THis could be an expensive operations if remote, so may need
            # caching or maybe remote resolution?
            if rendering_context:
                source_url = get_url_with_pkey(user_settings, file_url)
                content = get_file(source_url).decode('utf-8')  # FIXME: assume template are unicode, not bytestrings
                logger.debug("content=%s" % content)
                # Parse file parameter and retrieve data
                logger.debug("file_url %s" % file_url)
                # TODO: don't use temp file, use remote file with
                # name file_url with suffix based on the command job number?
                t = Template(content)
                logger.debug("rendering_context = %s" % rendering_context)
                con = Context(rendering_context)
                logger.debug("prerending content = %s" % t)
                local_url = get_new_local_url(file_url)  # TODO: make remote
                logger.debug("local_rul=%s" % local_url)
                rendered_content = t.render(con).encode('utf-8')
                logger.debug("rendered_content=%s" % rendered_content)
                dest_url = get_url_with_pkey(user_settings, local_url)
                put_file(dest_url, rendered_content)
            else:
                logger.debug("no render required")
                local_url = file_url
            #localfs.save(remote_file_path, ContentFile(cont.encode('utf-8')))  # NB: ContentFile only takes bytes
            #command_args.append((u'', remote_file_path.decode('utf-8')))
            command_args.append((u'', local_url))
            #_put_file(file_url, cont.encode('utf8'), fs)
            #command_args.append((u'', file_url))
    return command_args


class NCIStorage(SFTPStorage):

    def __init__(self, settings=None):
        import pkg_resources
        version = pkg_resources.get_distribution("django_storages").version
        if not version is "1.1.8":
            logger.warn("NCIStorage overrides version 1.1.8 of django_storages. found version %s" % version)

        super(NCIStorage, self).__init__()
        if 'params' in settings:
            super(NCIStorage, self).__dict__["_params"] = settings['params']
        if 'root' in settings:
            super(NCIStorage, self).__dict__["_root_path"] = settings['root']
        if 'host' in settings:
            super(NCIStorage, self).__dict__["_host"] = settings['host']
        super(NCIStorage, self).__dict__["_dir_mode"] = 0700
        print super(NCIStorage, self)


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
        except Exception, e:
            print e

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
    except KeyError:
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
        logger.warn(e)
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
        fs = NCIStorage(settings=ssh_settings)
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
        fs = NCIStorage(settings=ssh_settings)
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
    # FIXME: Will not work with individual files, not directories
    logger.debug("copy_directories %s -> %s" % (source_url, destination_url))
    source_scheme = urlparse(source_url).scheme
    http_source_url = get_http_url(source_url)
    source = urlparse(http_source_url)
    source_location = source.netloc
    source_path = source.path
    query = parse_qsl(source.query)
    query_settings = dict(x[0:] for x in query)

    http_destination_url = get_http_url(destination_url)
    destination_prefix = destination_url.split('?')[0]
    logger.debug("destination_prefix=%s" % destination_prefix)
    destination_suffix = ""
    destination = urlparse(http_destination_url)
    destination_query = destination.query
    if destination_query:
        destination_suffix = "?" + destination_url.split('?')[1]

    if source_path[0] == os.path.sep:
        source_path = source_path[1:]

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
        fs = NCIStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % source_scheme)
        return

    logger.debug("destination_suffix=%s" % destination_suffix)
    logger.debug("source_path=%s" % source_path)
    current_content = fs.listdir(source_path)
    if current_content:
        logger.debug("current_content=%s" % pformat(current_content))
    current_path_pointer = source_path
    logger.debug("current_path_pointer=%s" % current_path_pointer)
    file_path_holder = []
    dir_path_holder = []
    while len(current_content) > 0:
        for i in current_content[1]:
            logger.debug("i=%s" % i)
            file_path = str(os.path.join(current_path_pointer, i))
            logger.debug("file_path=%s" % file_path)
            file_path_holder.append(file_path)
            logger.debug("file_path=%s" % file_path)
            content = fs.open(file_path).read()  # Can't we just call get_file ?
            logger.debug("content loaded")
            updated_file_path = file_path[len(source_path) + 1:]
            logger.debug("updated_file_path=%s" % updated_file_path)
            curr_dest_url = os.path.join(destination_prefix, updated_file_path) \
                            + destination_suffix
            logger.debug("Current destination url %s" % curr_dest_url)
            put_file(curr_dest_url, content)
        for j in current_content[0]:
            logger.debug("j=%s" % j)
            list = [os.path.join(current_path_pointer, j), True]
            logger.debug("list=%s" % list)
            dir_path_holder.append(list)
            logger.debug("dir_path_holder=%s" % dir_path_holder)

        current_content = []
        for k in dir_path_holder:
            if k[1]:
                k[1] = False
                current_path_pointer = k[0]
                current_content = fs.listdir(current_path_pointer)
                logger.debug("Current pointer %s " % current_path_pointer)
                break
    logger.debug("All files")
    logger.debug(file_path_holder)
    logger.debug(dir_path_holder)
    logger.debug("end of copy_directories")

# def copy_files_with_pattern(self, local_filesystem, source_dir,
#                              dest_dir, pattern, overwrite=True):
#     import fnmatch, fs
#     pattern_source_dir = path.join(
#         local_filesystem, source_dir)
#     for file in self.connector_fs.listdir(pattern_source_dir):
#         if fnmatch.fnmatch(file, pattern):
#             try:
#                 logger.debug("To be copied %s " % os.path.join(pattern_source_dir,
#                     file))
#                 logger.debug("Dest %s " % os.path.join(dest_dir, file))
#                 self.connector_fs.copy(path.join(pattern_source_dir,
#                     file),
#                     path.join(dest_dir, file),
#                     overwrite)
#             except ResourceNotFoundError, e:
#                 import sys, traceback
#                 traceback.print_exc(file=sys.stdout)

#                 raise IOError(e)  # FIXME: make filesystem specfic exceptions


def put_file(file_url, content):
    """
    Writes out the content to the file_url using config info from user_settings. Note that content is bytecodes
    """
    logger.debug("file_url=%s" % file_url)
    if '..' in file_url:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")
    scheme = urlparse(file_url).scheme
    http_file_url = get_http_url(file_url)
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
        fs = NCIStorage(settings=ssh_settings)
         # FIXME: does this overwrite?
        fs.save(mypath, ContentFile(content))  # NB: ContentFile only takes bytes
        logger.debug("File to be written on %s" % location)
    elif scheme == "tardis":
        logger.warn("tardis put not implemented")
        #raise NotImplementedError()
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
        fs = NCIStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
    else:
        logger.warn("scheme: %s not supported" % source_scheme)
        return

    logger.debug("source_path=%s"  % source_path)

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


def get_filep(file_url):
    """
    opens a django file pointer to file_url
    """
    logger.debug("file_url=%s" % file_url)
    if '..' in file_url:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")
    scheme = urlparse(file_url).scheme
    http_file_url = get_http_url(file_url)
    o = urlparse(http_file_url)
    mypath = str(o.path)
    location = o.netloc

    # TODO: add error checking for urlparse
    logger.debug("scheme=%s" % scheme)
    logger.debug("mypath=%s" % mypath)

    if mypath[0] == os.path.sep:
        mypath = str(mypath[1:])
    logger.debug("mypath=%s" % mypath)
    query = parse_qsl(o.query)
    query_settings = dict(x[0:] for x in query)

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
        if not key_file:
            key_file = None  # require None for ssh_settings to skip keys

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
        fs = NCIStorage(settings=ssh_settings)
        logger.debug("fs=%s" % fs)
        logger.debug("mypath=%s" % mypath)
        fp = fs.open(mypath)
        logger.debug("fp opened")
        #content = fp.read()
        #logger.debug("content=%s" % content)
    elif scheme == "tardis":
        return "a={{a}} b={{b}}"
        raise NotImplementedError("tardis scheme not implemented")
    elif scheme == "file":
        root_path = get_value('root_path', query_settings)
        logger.debug("self.root_path=%s" % root_path)
        fs = LocalStorage(location=root_path + "/")
        fp = fs.open(mypath)
        #content = fs.open(mypath).read()
        #logger.debug("content=%s" % content)
    return fp



def transfer(old, new):
    """
    Transfer new dict into new dict at two levels by items rather than wholesale
    update (which would overwrite at the second level)
    """
    for k, v in new.items():
        for k1, v1 in v.items():
            if not k in old:
                old[k] = {}
            old[k][k1] = v1
    return old

def check_settings_valid(settings_to_test, user_settings, command):
    """
    Check that the run_settings and stage_settings for a stage are
    valid before scheduling to detect major errors before runtime
    """

    children = models.Stage.objects.filter(parent=command.stage)
    if children:
        stageset = children
    else:
        stageset = [command.stage]
    for current_stage in stageset:
        stage_settings = current_stage.get_settings()
        settings_to_test = transfer(stage_settings, settings_to_test)
        try:
            stage = safe_import(current_stage.package, [],
                {'user_settings': user_settings})
        except ImproperlyConfigured,e:
            return (False, "Except in import of stage: %s: %s"
                % (current_stage.name, e))
        logger.debug("stage=%s", stage)
        is_valid, problem = stage.input_valid(settings_to_test)
        if not is_valid:
            return (False, "precondition error in stage: %s: %s"
                % (current_stage.name, problem))
    return (True, "ok")


def make_runcontext_for_directive(platform_name, directive_name,
    directive_args, initial_settings, username):
    """
    Create a new runcontext with the commmand equivalent to the directive
    on the platform.
    """
    logger.debug("Platform Name %s" % platform_name)
    user = User.objects.get(username=username)  # FIXME: pass in username
    logger.debug("user=%s" % user)
    profile = models.UserProfile.objects.get(user=user)
    logger.debug("profile=%s" % profile)

    platform = models.Platform.objects.get(name=platform_name)
    logger.debug("platform=%s" % platform)

    run_settings = dict(initial_settings)  # we may share initial_settings

    directive = models.Directive.objects.get(name=directive_name)
    logger.debug("directive=%s" % directive)
    command_for_directive = models.Command.objects.get(directive=directive,
        platform=platform)
    logger.debug("command_for_directive=%s" % command_for_directive)
    user_settings = retrieve_settings(profile)
    logger.debug("user_settings=%s" % pformat(user_settings))
    # turn the user's arguments into real command arguments.

    command_args = _get_command_actual_args(
        directive_args, user_settings)
    logger.debug("command_args=%s" % command_args)

    run_settings = _make_run_settings_for_command(command_for_directive,
        command_args, run_settings)
    logger.debug("updated run_settings=%s" % run_settings)

    settings_valid, problem = check_settings_valid(run_settings,
        user_settings,
        command_for_directive)
    if not settings_valid:
        raise InvalidInputError(problem)

    system = {u'platform': platform_name, u'contextid': 0}
    run_settings[u'http://rmit.edu.au/schemas/system'] = system

    run_context = _make_new_run_context(command_for_directive.stage,
        profile, run_settings)
    logger.debug("run_context =%s" % run_context)
    run_context.current_stage = command_for_directive.stage
    run_context.save()

    run_settings[u'http://rmit.edu.au/schemas/system'][u'contextid'] = run_context.id

    # Add the run_context id as suffix to the current output_location
    output_location = run_settings['http://rmit.edu.au/schemas/system/misc']['output_location']
    run_settings[u'http://rmit.edu.au/schemas/system/misc']['output_location'] = "%s%s" % (output_location, run_context.id)
    run_context.update_run_settings(run_settings)

    logger.debug("command=%s new runcontext=%s" % (command_for_directive, run_context))
    # FIXME: only return command_args and context because they are needed for testcases
    return (run_settings, command_args, run_context)


def _make_new_run_context(stage, profile, run_settings):
    """
    Make a new context  for a user to execute stages based on initial context
    """
    # make run_context for this user
    run_context = models.Context.objects.create(owner=profile,
        current_stage=stage)
    run_context.update_run_settings(run_settings)
    return run_context

@deprecated
def process_all_contexts():
    """
    The main processing loop.  For each context owned by a user, find the next stage to execute,
    get the actual code to execute, then update the context and the filesystem as needed, then advance
    current stage according to the composite stage structure.
    TODO: this loop will run continuously as celery task to take Directives into commands into contexts
    for execution.
    """
    logger.warn("process_contexts_context is deprecated")
    test_info = []
    while (True):
        run_contexts = models.Context.objects.all()
        if not run_contexts:
            break
        done = None
        for run_context in run_contexts:
            # retrive the stage model to process
            current_stage = run_context.current_stage
            logger.debug("current_stage=%s" % current_stage)

            profile = run_context.owner
            logger.debug("profile=%s" % profile)

            run_settings = run_context.get_context()
            logger.debug("retrieved run_settings=%s" % run_settings)

            user_settings = retrieve_settings(profile)
            logger.debug("user_settings=%s" % user_settings)

            # FIXME: do we want to combine cont and user_settings to
            # pass into the stage?  The original code but the problem is separating them
            # again before they are serialised.

            # get the actual stage object
            stage = safe_import(current_stage.package, [],
             {'user_settings': user_settings})  # obviously need to cache this
            logger.debug("stage=%s", stage)

            if stage.triggered(run_settings):
                logger.debug("triggered")
                stage.process(run_settings)
                run_settings = stage.output(run_settings)
                logger.debug("updated run_settings=%s" % run_settings)
                run_context.update_run_settings(run_settings)
                logger.debug("run_settings=%s" % run_settings)
            else:
                logger.debug("not triggered")

            # advance to the next stage
            current_stage = run_context.current_stage.get_next_stage(run_settings)
            if not current_stage:
                done = run_context
                break

            # save away new stage to process
            run_context.current_stage = current_stage
            run_context.save()
        if done:
            test_info.append(run_settings)
            run_context.delete()
    logger.debug("finished main loop")
    return test_info


def _make_run_settings_for_command(command, command_args, run_settings):
    """
    Create run_settings for the command to execute with
    """
    if u'http://rmit.edu.au/schemas/system/misc' in run_settings:
        misc = run_settings[u'http://rmit.edu.au/schemas/system/misc']
    else:
        misc = {}

    if u'transitions' in misc:
        curr_trans = json.loads(misc[u'transitions'])
        logger.debug("curr_trans = %s" % curr_trans)
    else:
        curr_trans = {}

    #context = {}
    arg_num = 0
    file_args = {}
    config_args = collections.defaultdict(dict)
    for (k, v) in command_args:
        logger.debug("k=%s,v=%s" % (k, v))
        if k:
            config_args[os.path.dirname(k)][os.path.basename(k)] = v
        else:
            file_args['file%s' % arg_num] = v
            arg_num += 1

    run_settings[u'http://rmit.edu.au/schemas/%s/files' % command.directive.name] = file_args
    run_settings.update(config_args)

    logger.debug("run_settings=%s" % run_settings)
    transitions = models.make_stage_transitions(command.stage)
    logger.debug("transitions=%s" % transitions)
    transitions.update(curr_trans)

    if u'http://rmit.edu.au/schemas/system/misc' in run_settings:
        misc = run_settings[u'http://rmit.edu.au/schemas/system/misc']
    else:
        misc = {}
        run_settings[u'http://rmit.edu.au/schemas/system/misc'] = misc
    misc[u'transitions'] = json.dumps(transitions, ensure_ascii=True)

    logger.debug("run_settings =  %s" % run_settings)
    return run_settings


def retrieve_private_key(settings, private_key_url):
    """
    Gets the private key from url and stores in local file
    """
    # TODO: cache this result, because function used often
    # TODO/FIXME: need ability to delete this key, because
    # is senstive.  For example, delete at end of each stage execution.
    url = smartconnector.get_url_with_pkey(settings,
        private_key_url)
    logger.debug("url=%s" % url)
    key_contents = get_file(url)
    local_url = smartconnector.get_url_with_pkey(settings,
        os.path.join("centos", 'key'), is_relative_path=True)
    logger.debug("local_url=%s" % local_url)
    put_file(local_url, key_contents)
    private_key_file = get_remote_path(local_url)
    logger.debug("private_key_file=%s" % private_key_file)
    return private_key_file



def generate_rands(settings, start_range,  end_range, num_required, start_index):
    # FIXME: there must be an third party library that does this more
    # effectively.
    rand_nums = []
    num_url = get_url_with_pkey(settings, settings['random_numbers'],
        is_relative_path=False)
    random_content = get_file(num_url)
    # FIXME: this loads the entire file, which could be very large.
    numbers = random_content.split('\n')

    random_counter = start_index
    # FIXME: better handled with separate function
    if end_range < start_range:
        # special case, where we want rands in range of number of rands in file
        start_range = 0
        end_range = len(numbers)

    for i in range(0, num_required):

        raw_num = float(numbers[random_counter])
        num = int((raw_num * float(end_range - start_range)) + start_range)

        rand_nums.append(num)
        logger.debug("[0,1) %s -> [%s,%s) %s" % (raw_num, start_range, end_range, num))

        random_counter += 1
        if random_counter >= len(numbers):
            random_counter = 0

    # for i, line in enumerate(random_content.split('\n')):
    #     if start_index <= i < (start_index + num_required):
    #         raw_num = float(line)
    #         num = int((raw_num * float(end_range - start_range)) + start_range)
    #         logger.debug("[0,1) %s -> [%s,%s) %s" % (raw_num, start_range, end_range, num))
    #         rand_nums.append(num)

    logger.debug("Generated %s random numbers from %s in range [%s, %s): %s "
        % (num_required, num_url, start_range, end_range, pformat(rand_nums)))
    return rand_nums

@deprecated
def clear_temp_files(context):
    """
    Deletes "default" files from filesystem
    """
    filesystem = get_filesys(context)
    print "Deleting temporary files ..."
    filesystem.delete_local_filesystem('default')
    print "done."


def test_task():
    print "Hello World"
