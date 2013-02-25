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

# Contains the specific connectors and stages for HRMC

import sys
import os
import time
import logging
import logging.config
import json
import os
import sys
import re

from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.core.files.base import ContentFile

from django.contrib.auth.models import User



logger = logging.getLogger(__name__)

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI, SmartConnector
from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import create_environ, \
    collect_instances, destroy_environ
from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing, InvalidInputError
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler import models

from django.core.files.storage import FileSystemStorage

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from storages.backends.sftpstorage import SFTPStorage

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
            logger.error("Invalid settings values found for %s"% param)
            raise BadInputException()
        logger.debug("%s %s %s" % (param.paramset.schema, param.name,
            param.getValue()))

    return settings


def get_file_from_context(context, fname):
    """
    Retrieve the content of a remote file with fname
    """
    fsys_path = context['fsys']
    remote_fs = FileSystemStorage(location=fsys_path)
    f = context[fname]
    content = remote_fs.open(f).read()
    return content

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
    except ContextKeyMissing, e:
        logger.debug('ContextKeyMissing exception')
        raise


def _get_run_info_file(context):
    """
    Returns the actual runinfo data object. If problem, return blank data object
    """
    fsys = get_filesys(context)
    #logger.debug("fsys= %s" % fsys)
    config = _load_file(fsys, "default/runinfo.sys")
    #logger.debug("config= %s" % config)
    return config


def get_run_info(context):
    """
    Returns the content of the run info as file a dict. If problem, return {}
    """
    try:
        fsys = get_filesys(context)
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


def get_all_settings(context):
    """
    Returns a single dict containing content of config.sys and runinfo.sys
    """
    settings = get_settings(context)
    run_info = get_run_info(context)
    settings.update(run_info)
    settings.update(context)
    return settings


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


def _get_new_local_url(url):
    """
    Create local resource to hold instantiated template for command execution.

    """

    # # The top of the remote filesystem that will hold a user's files
    remote_base_path = os.path.join("centos")

    from urlparse import urlparse
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
    return u'local://%s' % dest_path.decode('utf8')


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
                    metadata_schema = models.Schema.objects.get(namespace=sch)
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

                        if file_url:
                            rendering_context[k.decode('utf8')] = typed_val
                        else:
                            command_args.append((k.decode('utf8'), typed_val))

        # retrieve the file url and resolve against rendering_context
        if file_url:
            # THis could be an expensive operations if remote, so may need
            # caching or maybe remote resolution?
            content = _get_file(file_url, user_settings)
            # Parse file parameter and retrieve data
            logger.debug("file_url %s" % file_url)
            # TODO: don't use temp file, use remote file with
            # name file_url with suffix based on the command job number?
            t = Template(content)
            logger.debug("rendering_context = %s" % rendering_context)
            con = Context(rendering_context)
            local_url = _get_new_local_url(file_url)  # TODO: make remote
            logger.debug("local_rul=%s" % local_url)
            rendered_content = t.render(con)
            _put_file(local_url, rendered_content, user_settings)
            #localfs.save(remote_file_path, ContentFile(cont.encode('utf-8')))  # NB: ContentFile only takes bytes
            #command_args.append((u'', remote_file_path.decode('utf-8')))
            command_args.append((u'', local_url))
            #_put_file(file_url, cont.encode('utf8'), fs)
            #command_args.append((u'', file_url))
    return command_args


class NCIStorage(SFTPStorage):

    def __init__(self, settings=None):
        super(NCIStorage, self).__init__()
        if 'params' in settings:
            super(NCIStorage, self).__dict__["_params"] = settings['params']
        if 'root' in settings:
            super(NCIStorage, self).__dict__["_root_path"] = settings['root']
        if 'host' in settings:
            super(NCIStorage, self).__dict__["_host"] = settings['host']
        print super(NCIStorage, self)


def _put_file(file_url, content, user_settings):
    """
    Writes out the content to the file url
    """
    logger.debug("file_url=%s" % file_url)

    logger.debug("file_url=%s" % file_url)
    from urlparse import urlparse
    o = urlparse(file_url)
    scheme = o.scheme
    mypath = o.path
    if mypath[0] == os.path.sep:
        mypath = mypath[1:]
    logger.debug("mypath=%s" % mypath)

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
    elif scheme == "hpc":
        remote_fs_path = os.path.join(
            os.path.dirname(__file__), '..', 'testing', 'remotesys').decode("utf8")
        nci_settings = {'params': {'username': user_settings['nci_user'],
            'password': user_settings['nci_password']},
            'host': user_settings['nci_host'],
            'root': remote_fs_path}
        fs = NCIStorage(settings=nci_settings)
         # FIXME: does this overwrite?
        fs.save(mypath, ContentFile(content.encode('utf-8')))  # NB: ContentFile only takes bytes
    elif scheme == "tardis":
        logger.warn("tardis put not implemented")
        #raise NotImplementedError()
    elif scheme == "local":
        remote_fs_path = user_settings['fsys']
        logger.debug("remote_fs_path=%s" % remote_fs_path)
        fs = FileSystemStorage(location=remote_fs_path)
        dest_path = fs.save(mypath, ContentFile(content.encode('utf-8')))  # NB: ContentFile only takes bytes
        logger.debug("dest_path=%s" % dest_path)
    return content


def _get_file(file_url, user_settings):
    """
    """
    logger.debug("file_url=%s" % file_url)

    from urlparse import urlparse
    o = urlparse(file_url)
    scheme = o.scheme
    mypath = o.path
    logger.debug("scheme=%s" % scheme)
    logger.debug("mypath=%s" % mypath)

    if mypath[0] == os.path.sep:
        mypath = mypath[1:]
    logger.debug("mypath=%s" % mypath)

    if scheme == 'http':
        import urllib2
        req = urllib2.Request(o)
        response = urllib2.urlopen(req)
        content = response.read()
    elif scheme == "hpc":
        logger.debug("getting from hpc")
        # TODO: remote_fs_path should be from user settings
        remote_fs_path = os.path.join(
            os.path.dirname(__file__), 'testing', 'remotesys')
        logger.debug("remote_fs_path=%s" % remote_fs_path)

        nci_settings = {'params': {'username': user_settings['nci_user'],
            'password': user_settings['nci_password']},
            'host': user_settings['nci_host'],
            'root': remote_fs_path}
        fs = NCIStorage(settings=nci_settings)
        content = fs.open(mypath).read()
        logger.debug("content=%s" % content)
    elif scheme == "tardis":
        return "a={{a}} b={{b}}"
        raise NotImplementedError("tardis scheme not implemented")
    elif scheme == "local":
        remote_fs_path = user_settings['fsys']
        logger.debug("self.remote_fs_path=%s" % remote_fs_path)
        fs = FileSystemStorage(location=remote_fs_path + "/")
        content = fs.open(mypath).read()
    logger.debug("content=%s" % content)
    return content


def make_runcontext_for_directive(platform, directive_name,
    directive_args):
    # get the user
    user = User.objects.get(username="username1")
    profile = models.UserProfile.objects.get(user=user)
    platform = models.Platform.objects.get(name=platform)
    directive = models.Directive.objects.get(name=directive_name)
    command_for_directive = models.Command.objects.get(directive=directive, platform=platform)
    logger.debug("commandnd_for_directive=%s" % command_for_directive)
    user_settings = retrieve_settings(profile)

    # turn the user's arguments into real command arguments.
    command_args = _get_command_actual_args(
        directive_args, user_settings)
    logger.debug("command_args=%s" % command_args)
    # prepare a context for the command to run for this user
    context = _make_context_for_command(command_for_directive,
        command_args)
    run_context = _make_new_run_context(command_for_directive.stage, profile, context)
    run_context.current_stage = command_for_directive.stage
    run_context.save()
    # FIXME: only return command_args and context  because needed for testcases
    return (context, command_args, run_context)


def _make_new_run_context(stage, profile, context):
    """
    Make a new context  for a user to execute stages based on initial context
    """
    # make run_context for this user
    run_context = models.Context.objects.create(owner=profile,
        current_stage=stage)
    context_schema = models.Schema.objects.get(namespace=models.Context.CONTEXT_SCHEMA_NS)
    logger.debug("context_schema=%s" % context_schema)
    # make a single parameterset to represent the context
    models.ContextParameterSet.objects.create(context=run_context,
        schema=context_schema,
        ranking=0)
    run_context.update_context(context)
    return run_context


def process_all_contexts():
    """
    The main processing loop.  For each context owned by a user, find the next stage to execute,
    get the actual code to execute, then update the context and the filesystem as needed, then advance
    current stage according to the composite stage structure.
    TODO: this loop will run continuously as celery task to take Directives into commands into contexts
    for execution.
    """
    done = False
    while (True):
        for run_context in models.Context.objects.all():
            # retrive the stage model to process
            current_stage = run_context.current_stage
            logger.debug("current_stage=%s" % current_stage)

            profile = run_context.owner
            logger.debug("profile=%s" % profile)

            cont = run_context.get_context()
            logger.debug("retrieved cont=%s" % cont)

            user_settings = retrieve_settings(profile)
            logger.debug("user_settings=%s" % user_settings)

            # FIXME: do we want to combine cont and user_settings to
            # pass into the stage?  The original code but the problem is separating them
            # again before they are serialised.

            # get the actual stage object
            stage = safe_import(current_stage.package,  [], {})  # obviously need to cache this
            logger.debug("stage=%s", stage)

            if stage.triggered(cont):
                logger.debug("triggered")
                stage.process(cont)
                cont = stage.output(cont)
                logger.debug("updated cont=%s" % cont)
                run_context.update_context(cont)
                logger.debug("cont=%s" % cont)
            else:
                logger.debug("not triggered")

            # advance to the next stage
            current_stage = run_context.current_stage.get_next_stage(cont)
            if not current_stage:
                done = True
                break

            # save away new stage to process
            run_context.current_stage = current_stage
            run_context.save()
        if done:
            break
    logger.debug("finished main loop")


def _make_context_for_command(command, command_args):
    """
    Create a context for the command to execute with
    """
    context = {}
    arg_num = 0
    for (k, v) in command_args:
        logger.debug("k=%s,v=%s" % (k, v))
        if k:
            context[k] = v
        else:
            key = u"file%s" % arg_num
            arg_num += 1
            context[key] = v
    logger.debug("context=%s" % context)
    transitions = models.make_parallel_stage(command.stage, context)
    logger.debug("transitions=%s" % transitions)
    context[u'transitions'] = json.dumps(transitions)
    logger.debug("context =  %s" % context)
    return context


def clear_temp_files(context):
    """
    Deletes "default" files from filesystem
    """
    filesystem = get_filesys(context)
    print "Deleting temporary files ..."
    filesystem.delete_local_filesystem('default')
    print "done."
