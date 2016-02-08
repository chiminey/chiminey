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

# Contains the specific connectors and corestages for HRMC

import os
import logging
import json
import collections
from pprint import pformat
from django.db import transaction

from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from storages.backends.sftpstorage import SFTPStorage

from chiminey.smartconnectorscheduler.errors \
    import ContextKeyMissing, InvalidInputError, deprecated, BadInputException
from chiminey.smartconnectorscheduler import models
from chiminey.storage import get_url_with_credentials, get_file

from chiminey import messages

logger = logging.getLogger(__name__)


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
    return command_args



def transfer(old, new):
    """
    Transfer new dict into new dict at two levels by items rather than wholesale
    update (which would overwrite at the second level)
    """
    for k, v in new.iteritems():
        for k1, v1 in v.iteritems():
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
    stageset = [thestage]
    if children:
        stageset.extend(children)

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
            logger.debug("precondition error in stage: %s: %s"
                % (current_stage.name, problem))
            return (False, problem)
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

    try:
        settings_valid, problem = check_settings_valid(run_settings,
            user_settings,
            directive.stage)
    except Exception, e:
        import traceback
        tc = traceback.format_exc()
        logger.error(e)
        logger.error(tc)
        messages.error(run_settings, "0: internal error (%s stage):%s" % (directive.stage.name, e))
        raise InvalidInputError("0: internal error (%s stage):%s" % (directive.stage.name, e))

    if not settings_valid:
        raise InvalidInputError(problem)

    run_settings[u'http://rmit.edu.au/schemas/system'][u'platform'] = platform_name
    run_settings[u'http://rmit.edu.au/schemas/system'][u'contextid'] = 0

    run_context = _make_new_run_context(directive.stage,
        profile, directive, parent, run_settings)
    logger.debug("run_context =%s" % run_context)
    run_context.current_stage = directive.stage
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
    Make a new context  for a user to execute corestages based on initial context
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
#     url = smartconnectorscheduler.get_url_with_credentials(settings,
#         private_key_url)
#     logger.debug("url=%s" % url)
#     key_contents = get_file(url)
#     local_url = smartconnectorscheduler.get_url_with_credentials(settings,
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
    num_url = get_url_with_credentials(settings, settings['random_numbers'],
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

    for i in xrange(0, num_required):

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
