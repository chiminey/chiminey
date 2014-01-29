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

# Contains the specific connectors and stages for HRMC

import os
import logging
import logging.config
import json
import time
import collections
from pprint import pformat
import paramiko
import getpass
from urlparse import urlparse, parse_qsl
from django.db import transaction

from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from storages.backends.sftpstorage import SFTPStorage

from paramiko.ssh_exception import SSHException

from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing, InvalidInputError, deprecated
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import storage

logger = logging.getLogger(__name__)



# @deprecated
# def get_filesys(context):
#     """
#     Return the filesys in the context
#     """
#     try:
#         val = context['filesys']
#     except KeyError:
#         message = 'Context missing "filesys" key'
#         logger.exception(message)
#         raise ContextKeyMissing(message)
#     return val


# @deprecated
# def _load_file(fsys, fname):
#     """
#     Returns the dataobject for fname in fsys, or empty data object if error
#     """
#     try:
#         config = fsys.retrieve(fname)
#     except KeyError, e:
#         config = DataObject(fname, '')
#         logger.warn("Cannot load %s %s" % (fname, e))
#     return config


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


# @deprecated
# def get_file_from_context(context, fname):
#     """
#     Retrieve the content of a remote file with fname
#     """
#     fsys_path = context['fsys']
#     remote_fs = FileSystemStorage(location=fsys_path)
#     f = context[fname]
#     content = remote_fs.open(f).read()
#     return content


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


# @deprecated
# def _get_run_info_file(context):
#     """
#     Returns the actual runinfo data object. If problem, return blank data object
#     """
#     fsys = get_filesys(context)
#     #logger.debug("fsys= %s" % fsys)
#     config = _load_file(fsys, "default/runinfo.sys")
#     #logger.debug("config= %s" % config)
#     return config


# @deprecated
# def get_run_info(context):
#     """
#     Returns the content of the run info as file a dict. If problem, return {}
#     """
#     try:
#         get_filesys(context)
#     except ContextKeyMissing:
#         return {}
#     #logger.debug("fsys= %s" % fsys)
#     config = _get_run_info_file(context)
#     #logger.debug("config= %s" % config)
#     if config:
#         settings_text = config.retrieve()
#         #logger.debug("runinfo_text= %s" % settings_text)
#         res = json.loads(settings_text)
#         #logger.debug("res=%s" % dict(res))
#         return dict(res)
#     return {}


# # @deprecated
# # def get_all_settings(context):
# #     """
# #     Returns a single dict containing content of config.sys and runinfo.sys
# #     """
# #     settings = get_settings(context)
# #     run_info = get_run_info(context)
# #     settings.update(run_info)
# #     settings.update(context)
# #     return settings


# @deprecated
# def update_key(key, value, context):
#     """
#     Updates key from the filesystem runinfo.sys file to a new values
#     """
#     filesystem = get_filesys(context)
#     logger.debug("filesystem= %s" % filesystem)

#     run_info_file = _load_file(filesystem, "default/runinfo.sys")
#     logger.debug("run_info_file= %s" % run_info_file)

#     run_info_file_content = run_info_file.retrieve()
#     logger.debug("runinfo_content= %s" % run_info_file_content)

#     settings = json.loads(run_info_file_content)
#     logger.debug("removing %s" % key)
#     settings[key] = value  # FIXME: possible race condition?
#     logger.debug("configuration=%s" % settings)

#     run_info_content_blob = json.dumps(settings)
#     run_info_file.setContent(run_info_content_blob)
#     filesystem.update("default", run_info_file)


# @deprecated
# def delete_key(key, context):
#     """
#     Removes key from the filesystem runinfo.sys file
#     """
#     filesystem = get_filesys(context)
#     logger.debug("filesystem= %s" % filesystem)

#     run_info_file = _load_file(filesystem, "default/runinfo.sys")
#     logger.debug("run_info_file= %s" % run_info_file)

#     run_info_file_content = run_info_file.retrieve()
#     logger.debug("runinfo_content= %s" % run_info_file_content)

#     settings = json.loads(run_info_file_content)
#     del settings[key]
#     logger.debug("configuration=%s" % settings)

#     run_info_content_blob = json.dumps(settings)
#     run_info_file.setContent(run_info_content_blob)
#     filesystem.update("default", run_info_file)


# def get_fanout(parameter_value_list):
#     '''
#     total_fanout = 1
#     if len(self.threshold) > 1:
#         for i in self.threshold:
#             total_fanout *= self.threshold[i]
#     else:
#         total_picks = self.threshold[0]
#     '''
#     pass


# @deprecated
# def get_job_dir_old(run_settings):
#     output_storage_schema = run_settings['http://rmit.edu.au/schemas/platform/storage/output']['namespace']
#     ip_address = run_settings[output_storage_schema][u'ip_address']
#     offset = run_settings[output_storage_schema][u'offset']
#     job_dir = os.path.join(ip_address, offset)
#     return job_dir


def get_threshold():
    pass


def safe_import(path, args, kw):
    """
        Dynamically imports a package at path and executes it current namespace with given args
    """
    logger.debug(path)
    logger.debug("path %s args %s kw %s  " % (path, args, kw))
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a filter module' % path)
    filter_module, filter_classname = path[:dot], path[dot + 1:]
    logger.debug("filter_module=%s filter_classname=%s" % (filter_module, filter_classname))
    try:
        mod = import_module(filter_module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing stage %s: "%s"' %
                                   (filter_module, e))
    logger.debug("mod=%s" % mod)
    try:
        filter_class = getattr(mod, filter_classname)
    except AttributeError:
        raise ImproperlyConfigured('Filter module "%s" does not define a "%s" class' %
                                   (filter_module, filter_classname))
    logger.debug("filter_class=%s" % filter_class)

    filter_instance = filter_class(*args, **kw)
    logger.debug("filter_instance=%s" % filter_instance)

    return filter_instance


def values_match_schema(schema, values):
    """
        Given a schema object and a set of (k,v) fields, checking
        each k has correspondingly named ParameterName in the schema
    """
    # TODO:
    return True


# def get_new_local_url(url):
#     """
#     Create local resource to hold instantiated template for command execution.

#     """

#     # # The top of the remote filesystem that will hold a user's files
#     remote_base_path = os.path.join("centos")

#     o = urlparse(url)
#     file_path = o.path.decode('utf-8')
#     logger.debug("file_path=%s" % file_path)
#     # if file_path[0] == os.path.sep:
#     #     file_path = file_path[:-1]
#     import uuid
#     randsuffix = unicode(uuid.uuid4())  # should use some job id here

#     relpath = u"%s_%s" % (file_path, randsuffix)

#     if relpath[0] == os.path.sep:
#         relpath = relpath[1:]
#     logger.debug("relpath=%s" % relpath)

#     # FIXME: for django storage, do we need to create
#     # intermediate directories
#     dest_path = os.path.join(remote_base_path, relpath)
#     logger.debug("dest_path=%s" % dest_path)
#     return u'file://%s' % dest_path.decode('utf8')


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
                        logger.debug("schema_namespace=%s" % sch)
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
        # if file_url:
        #     # THis could be an expensive operations if remote, so may need
        #     # caching or maybe remote resolution?
        #     if rendering_context:
        #         source_url = get_url_with_pkey(user_settings, file_url)
        #         content = get_file(source_url).decode('utf-8')  # FIXME: assume template are unicode, not bytestrings
        #         logger.debug("content=%s" % content)
        #         # Parse file parameter and retrieve data
        #         logger.debug("file_url %s" % file_url)
        #         # TODO: don't use temp file, use remote file with
        #         # name file_url with suffix based on the command job number?
        #         t = Template(content)
        #         logger.debug("rendering_context = %s" % rendering_context)
        #         con = Context(rendering_context)
        #         logger.debug("prerending content = %s" % t)
        #         local_url = get_new_local_url(file_url)  # TODO: make remote
        #         logger.debug("local_rul=%s" % local_url)
        #         rendered_content = t.render(con).encode('utf-8')
        #         logger.debug("rendered_content=%s" % rendered_content)
        #         dest_url = get_url_with_pkey(user_settings, local_url)
        #         put_file(dest_url, rendered_content)
        #     else:
        #         logger.debug("no render required")
        #         local_url = file_url
        #     #localfs.save(remote_file_path, ContentFile(cont.encode('utf-8')))  # NB: ContentFile only takes bytes
        #     #command_args.append((u'', remote_file_path.decode('utf-8')))
        #     command_args.append((u'', local_url))
        #     #_put_file(file_url, cont.encode('utf8'), fs)
        #     #command_args.append((u'', file_url))
    return command_args


# @deprecated
# class NCIStorage(SFTPStorage):

#     def __init__(self, settings=None):
#         import pkg_resources
#         version = pkg_resources.get_distribution("django_storages").version
#         if not str(version) == "1.1.8":
#             logger.warn("NCIStorage overrides version 1.1.8 of django_storages. found version %s" % version)

#         super(NCIStorage, self).__init__()
#         if 'params' in settings:
#             super(NCIStorage, self).__dict__["_params"] = settings['params']
#         if 'root' in settings:
#             super(NCIStorage, self).__dict__["_root_path"] = settings['root']
#         if 'host' in settings:
#             super(NCIStorage, self).__dict__["_host"] = settings['host']
#         super(NCIStorage, self).__dict__["_dir_mode"] = 0700
#         print super(NCIStorage, self)

#     def _connect(self):
#         """ Overrides internal behaviour to not store host keys
#             Warning: may stop working for later version of SFTPStorage
#             FIXME: this approach is brittle for later version of SFTPStorage
#         """
#         self._ssh = paramiko.SSHClient()

#         if self._known_host_file is not None:
#             self._ssh.load_host_keys(self._known_host_file)
#         else:
#             # warn BUT DONT ADD host keys from current user.
#             self._ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

#         # and automatically add new host keys for hosts we haven't seen before.
#         self._ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

#         try:
#             self._ssh.connect(self._host, **self._params)
#         except paramiko.AuthenticationException, e:
#             if self._interactive and 'password' not in self._params:
#                 # If authentication has failed, and we haven't already tried
#                 # username/password, and configuration allows it, then try
#                 # again with username/password.
#                 if 'username' not in self._params:
#                     self._params['username'] = getpass.getuser()
#                 self._params['password'] = getpass.getpass()
#                 self._connect()
#             else:
#                 raise paramiko.AuthenticationException, e
#         except Exception, e:
#             print e

#         if not hasattr(self, '_sftp'):
#             self._sftp = self._ssh.open_sftp()

#     def get_available_name(self, name):
#         """
#         Returns a filename that's free on the target storage system, and
#         available for new content to be written to.
#         """
#         if self.exists(name):
#             self.delete(name)
#         return name


# @deprecated
# class LocalStorage(FileSystemStorage):
#     def __init__(self, location=None, base_url=None):
#         super(LocalStorage, self).__init__(location, base_url)

#     def get_available_name(self, name):
#         """
#         Returns a filename that's free on the target storage system, and
#         available for new content to be written to.
#         """
#         if self.exists(name):
#             self.delete(name)
#         return name


# @deprecated
# def get_http_url(non_http_url):
#     curr_scheme = non_http_url.split(':')[0]
#     http_url = "http" + non_http_url[len(curr_scheme):]
#     return http_url



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


def check_settings_valid(settings_to_test, user_settings, thestage):
    """
    Check that the run_settings and stage_settings for a stage are
    valid before scheduling to detect major errors before runtime
    """

    children = models.Stage.objects.filter(parent=thestage)
    if children:
        stageset = children
    else:
        stageset = [thestage]
    for current_stage in stageset:
        stage_settings = current_stage.get_settings()
        logger.debug("stage_settings=%s" % stage_settings)
        logger.debug("current_stage.package=%s" % current_stage.package)
        settings_to_test = transfer(stage_settings, settings_to_test)
        try:
            stage = safe_import(current_stage.package, [],
                {'user_settings': user_settings})
        except ImproperlyConfigured, e:
            return (False, "Except in import of stage: %s: %s"
                % (current_stage.name, e))
        logger.debug("stage=%s", stage)
        is_valid, problem = stage.input_valid(settings_to_test)
        if not is_valid:
            return (False, "precondition error in stage: %s: %s"
                % (current_stage.name, problem))
    return (True, "ok")


def make_runcontext_for_directive(platform_name, directive_name,
    directive_args, initial_settings, username, parent=None):
    """
    Create a new runcontext with the commmand equivalent to the directive
    on the platform.
    """
    logger.debug("directive_args=%s" % directive_args)
    logger.debug("Platform Name %s" % platform_name)
    user = User.objects.get(username=username)  # FIXME: pass in username
    logger.debug("user=%s" % user)
    profile = models.UserProfile.objects.get(user=user)
    logger.debug("profile=%s" % profile)

    #platform = models.Platform.objects.get(name=platform_name)
    #logger.debug("platform=%s" % platform)

    run_settings = dict(initial_settings)  # we may share initial_settings

    directive = models.Directive.objects.get(name=directive_name)
    logger.debug("directive=%s" % directive)

    # Have removed need to search on platform as should need to check platform
    # in this situation.
    # command_for_directive = models.Command.objects.get(directive=directive,
    #     platform=platform)
    # command_for_directive = models.Command.objects.get(directive=directive)
    # logger.debug("command_for_directive=%s" % command_for_directive)
    user_settings = retrieve_settings(profile)
    logger.debug("user_settings=%s" % pformat(user_settings))
    # turn the user's arguments into real command arguments.

    command_args = _get_command_actual_args(
        directive_args, user_settings)
    logger.debug("command_args=%s" % pformat(command_args))

    run_settings = _make_run_settings_for_command(command_args, run_settings)
    logger.debug("updated run_settings=%s" % run_settings)

    stage = directive.stage

    try:
        settings_valid, problem = check_settings_valid(run_settings,
            user_settings,
            stage)
    except Exception, e:
        logger.error(e)
        raise

    if not settings_valid:
        raise InvalidInputError(problem)

    run_settings[u'http://rmit.edu.au/schemas/system'][u'platform'] = platform_name
    run_settings[u'http://rmit.edu.au/schemas/system'][u'contextid'] = 0

    run_context = _make_new_run_context(stage,
        profile, directive, parent, run_settings)
    logger.debug("run_context =%s" % run_context)
    run_context.current_stage = stage
    run_context.save()

    run_settings[u'http://rmit.edu.au/schemas/system'][u'contextid'] = run_context.id

    # Add User settings to context, so we get set values when context executed
    # and local changes can be made to values in that context.
    run_settings[models.UserProfile.PROFILE_SCHEMA_NS] = user_settings

    run_context.update_run_settings(run_settings)

    logger.debug("new runcontext=%s" % (run_context))
    # FIXME: only return command_args and context because they are needed for testcases
    return (run_settings, command_args, run_context)


@transaction.commit_on_success
def _make_new_run_context(stage, profile, directive, parent, run_settings):
    """
    Make a new context  for a user to execute stages based on initial context
    """
    # make run_context for this user
    run_context = models.Context.objects.create(
        owner=profile,
        directive=directive,
        parent=parent,
        status="starting",
        current_stage=stage)
    if not parent:
        run_context.parent = run_context
        run_context.save()
    run_context.update_run_settings(run_settings)
    return run_context


# @deprecated
# def process_all_contexts():
#     """
#     The main processing loop.  For each context owned by a user, find the next stage to execute,
#     get the actual code to execute, then update the context and the filesystem as needed, then advance
#     current stage according to the composite stage structure.
#     TODO: this loop will run continuously as celery task to take Directives into commands into contexts
#     for execution.
#     """
#     logger.warn("process_contexts_context is deprecated")
#     test_info = []
#     while (True):
#         run_contexts = models.Context.objects.all()
#         if not run_contexts:
#             break
#         done = None
#         for run_context in run_contexts:
#             # retrive the stage model to process
#             current_stage = run_context.current_stage
#             logger.debug("current_stage=%s" % current_stage)

#             profile = run_context.owner
#             logger.debug("profile=%s" % profile)

#             run_settings = run_context.get_context()
#             logger.debug("retrieved run_settings=%s" % run_settings)

#             user_settings = retrieve_settings(profile)
#             logger.debug("user_settings=%s" % user_settings)

#             # FIXME: do we want to combine cont and user_settings to
#             # pass into the stage?  The original code but the problem is separating them
#             # again before they are serialised.

#             # get the actual stage object
#             stage = safe_import(current_stage.package, [],
#              {'user_settings': user_settings})  # obviously need to cache this
#             logger.debug("stage=%s", stage)

#             if stage.triggered(run_settings):
#                 logger.debug("triggered")
#                 stage.process(run_settings)
#                 run_settings = stage.output(run_settings)
#                 logger.debug("updated run_settings=%s" % run_settings)
#                 run_context.update_run_settings(run_settings)
#                 logger.debug("run_settings=%s" % run_settings)
#             else:
#                 logger.debug("not triggered")

#             # advance to the next stage
#             current_stage = run_context.current_stage.get_next_stage(run_settings)
#             if not current_stage:
#                 done = run_context
#                 break

#             # save away new stage to process
#             run_context.current_stage = current_stage
#             run_context.save()
#         if done:
#             test_info.append(run_settings)
#             run_context.delete()
#     logger.debug("finished main loop")
#     return test_info


def _make_run_settings_for_command(command_args, run_settings):
    """
    Create run_settings for the command to execute with
    """
    logger.debug("_make_run_settings_for_command")
    if u'http://rmit.edu.au/schemas/system/misc' in run_settings:
        misc = run_settings[u'http://rmit.edu.au/schemas/system/misc']
    else:
        misc = {}

    # Use of file arguments is deprecated as we use metadata arguments
    # for sending bdp urls and platform keys instead
    #arg_num = 0
    file_args = {}
    config_args = collections.defaultdict(dict)
    for (k, v) in command_args:
        logger.debug("k=%s,v=%s" % (k, v))
        if k:
            config_args[os.path.dirname(k)][os.path.basename(k)] = v
        # else:
        #     file_args['file%s' % arg_num] = v
        #     arg_num += 1

    #run_settings[u'http://rmit.edu.au/schemas/%s/files' % command.directive.name] = file_args
    run_settings.update(config_args)

    logger.debug("run_settings =  %s" % run_settings)
    return run_settings


# def retrieve_private_key(settings, private_key_url):
#     """
#     Gets the private key from url and stores in local file
#     """
#     # TODO: cache this result, because function used often
#     # TODO/FIXME: need ability to delete this key, because
#     # is senstive.  For example, delete at end of each stage execution.
#     url = smartconnector.get_url_with_pkey(settings,
#         private_key_url)
#     logger.debug("url=%s" % url)
#     key_contents = get_file(url)
#     local_url = smartconnector.get_url_with_pkey(settings,
#         os.path.join("centos", 'key'), is_relative_path=True)
#     logger.debug("local_url=%s" % local_url)
#     put_file(local_url, key_contents)
#     private_key_file = get_remote_path(local_url)
#     logger.debug("private_key_file=%s" % private_key_file)
#     return private_key_file


def generate_rands(settings, start_range,  end_range, num_required, start_index):
    # FIXME: there must be an third party library that does this more
    # effectively.
    rand_nums = []
    num_url = smartconnector.get_url_with_pkey(settings, settings['random_numbers'],
        is_relative_path=False)
    random_content = storage.get_file(num_url)
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



def get_parent_stage(child_package, settings):
    parent_obj = models.Stage.objects.get(package=child_package)
    parent_stage = parent_obj.parent
    try:
        logger.debug('parent_package=%s' % (parent_stage.package))
        stage = safe_import(parent_stage.package, [],
                                       {'user_settings': settings})
    except ImproperlyConfigured, e:
        logger.debug(e)
        return (False, "Except in import of stage: %s: %s"
            % (parent_stage.name, e))
    return stage
