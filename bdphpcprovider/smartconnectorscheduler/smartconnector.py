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

import os
import logging
import logging.config
from pprint import pformat

from urlparse import urlparse
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler.errors import deprecated
from bdphpcprovider.platform.manage import retrieve_platform
from django.contrib import messages

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


logger = logging.getLogger(__name__)


def copy_settings(dest_context, context, key):
    """
    """
    try:
        # Note that all run_settings and user_settings are flattened
        logger.debug('context=%s' % context[os.path.dirname(key)])
        res = context[os.path.dirname(key)][os.path.basename(key)]
        dest_context[os.path.basename(key)] = res
        logger.debug("dest_contxt[%s] = %s" % (os.path.basename(key), dest_context[os.path.basename(key)]))
    except KeyError:
        logger.error("error on key %s" % key)
        raise


def get_platform(platform_url):
    return get_bdp_storage_url(platform_url)


def get_bdp_storage_url(platform_url, username):
    platform_name = platform_url.split('/')[0]
    record, namespace = retrieve_platform(platform_name, username)
    logger.debug('record=%s' % record)
    return record, namespace


def get_url_with_pkey(settings, url_or_relative_path,
                      is_relative_path=False, ip_address='127.0.0.1'):
    '''
     This method appends private key, username, passowrd and/or rootpath
     parameters at end of a url. If only relative path is passed,
     a url is constructed based on the data @url_or_relative_path and
     @settings.

    Suppose
        url_or_relative_path = 'nectar@new_payload'
        is_relative_path = True
        ip_address = 127.0.0.1
        root_path = /home/centos
    the platform is nectar and the relative path is new_payload
    The new url will be ssh://127.0.0.1/new_payload?root_path=/home/centos

    #TODO: make testcase for above example.  This function has complicated
    #parameter values.
    :param settings:
    :param url_or_relative_path:
    :param is_relative_path:
    :param ip_address:
    :return:
    '''
    username = ''
    password = ''
    key_file = ''
    logger.debug("get_url_with_pkey(%s, %s, %s, %s)" % (
                 pformat(settings), url_or_relative_path,
                 is_relative_path, ip_address))

    if '..' in url_or_relative_path:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")

    if is_relative_path:
        url = 'http://' + url_or_relative_path
    else:
        url = url_or_relative_path
    parsed_url = urlparse(url)
    platform = parsed_url.username
    url_settings = {}
    logger.debug('platform=%s' % platform)
    if platform in ['nectar', 'unix', 'nci', 'csrack']:
        url_settings['username'] = settings['username']
        #url_settings['password'] = settings['nectar_password']
        url_settings['key_file'] = settings['private_key']
        # key_file = settings['nectar_private_key']
        # username = settings['nectar_username']
        # password = settings['nectar_password']
        url_settings['root_path'] = settings['root_path']

        args = '&'.join(["%s=%s" % (k, v) for k, v in sorted(url_settings.items())])
        scheme = 'ssh'

    # elif platform == 'nci':
    #     url_settings['username'] = settings['username']
    #     url_settings['password'] = settings['nci_password']
    #     url_settings['key_file'] = settings['nci_private_key']
    #     # key_file = settings['nci_private_key']
    #     # username = settings['nci_user']
    #     # password = settings['nci_password']

    #     scheme = 'ssh'
    elif platform == 'tardis':
        url_settings['mytardis_username'] = settings['mytardis_user']
        url_settings['mytardis_password'] = settings['mytardis_password']

        relative_path = parsed_url.path
        if relative_path[0] == os.path.sep:
            relative_path = relative_path[1:]

        if relative_path[-1] == os.path.sep:
            relative_path = relative_path[:-1]

        path_parts = relative_path.split(os.path.sep)
        logger.debug("path_parts=%s" % path_parts)
        username = path_parts[0]
        fname = path_parts[-1]
        dataset_name = path_parts[-2:-1]
        exp_name = path_parts[1:-2]
        url_settings['exp_name'] = os.sep.join(exp_name)
        url_settings['dataset_name'] = dataset_name[0]
        url_settings['username'] = username
        url_settings['fname'] = str(fname)

        scheme = 'tardis'

    elif not platform:
        platform = 'local'
        scheme = 'file'
    else:
        scheme = urlparse(url).scheme
        if scheme == 'file':
            platform = 'local'
        else:
            logger.debug("scheme [%s] unknown \n"
                         "Valid schemes [file, ssh]" % scheme)
            #raise NotImplementedError()
            return

    if platform == 'local':
        # fixme His gets the root path for the user's local file system.  This
        # could be hardcoded rather than using real platform object
        try:
            platform_object = models.Platform.objects.get(name=platform)  # fixme remove Platform model
            bdp_username = settings['bdp_username']
            logger.debug("bdp_username=%s" % bdp_username)
            root_path = os.path.join(platform_object.root_path, bdp_username)
            url_settings['root_path'] = root_path
        except models.Platform.DoesNotExist:
            logger.error('compatible platform for %s not found' % platform)

    # FIXME: URIs cannot contain unicode data, but IRI can. So need to convert IRI to URL
    # if parameters can be non-ascii
    # https://docs.djangoproject.com/en/dev/ref/unicode/#uri-and-iri-handling
    args = '&'.join(["%s=%s" % (k, v) for k, v in sorted(url_settings.items())])
    logger.debug("ip_address=%s" % ip_address)
    if is_relative_path:
        logger.debug("is_relative_path")
        partial_path = parsed_url.path
        if partial_path:
            if partial_path[0] == os.path.sep:
                partial_path = parsed_url.path[1:]
        # FIXME: for relative paths of subdirectories, X/Y, X cannot be upper case
        # TODO: don't use urlparse for relative paths, just break down manually
        relative_path = os.path.join(parsed_url.hostname, partial_path)
        logger.debug('host=%s path=%s relativepath=%s' % (parsed_url.hostname,
                                                          partial_path,
                                                          relative_path))

        # url_with_pkey = '%s://%s/%s?key_file=%s' \
        #                 '&username=%s&password=%s' \
        #                 '&root_path=%s' % (scheme, ip_address,
        #                                    relative_path, key_file,
        #                                    username, password, root_path)
        url_with_pkey = '%s://%s/%s?%s' % (scheme, ip_address,
                                           relative_path,
                                           args)
    else:
        # url_or_relative_path must be a valid url here,
        # which means we have to remove username, as it is a BDPurl.
        hostname = parsed_url.netloc
        logger.debug("hostname=%s" % hostname)
        relative_path = parsed_url.path

        # ip_address only used for relative url, otherwise extract from url
        if '@' in hostname:
            ip_address = hostname.split('@')[1]
            logger.debug("ip_address=%s" % ip_address)
        logger.debug("relative_path=%s" % relative_path)

        host = "%s://%s%s" % (scheme, ip_address, relative_path)

        url_with_pkey = '%s?%s' % (host, args)

        # url_with_pkey = '%s?key_filename=%s&username=%s' \
        #                 '&password=%s&root_path=%s' % (host, key_file,
        #                                                username, password,
        #                                                root_path)
    logger.debug("Final %s url_pkey %s" % (str(is_relative_path), url_with_pkey))
    return url_with_pkey


# def get_url_with_pkey(settings, url_or_relative_path,
#                       is_relative_path=False, ip_address='127.0.0.1'):
#     '''
#      This method appends private key, username, passowrd and/or rootpath
#      parameters at end of a url. If only relative path is passed,
#      a url is constructed based on the data @url_or_relative_path and
#      @settings.

#     Suppose
#         url_or_relative_path = 'nectar@new_payload'
#         ip_address = 127.0.0.1
#         root_path = /home/centos
#     the platform is nectar and the relative path is new_payload
#     The new url will be ssh://127.0.0.1/new_payload?root_path=/home/centos

#     :param settings:
#     :param url_or_relative_path:
#     :param is_destination:
#     :param ip_address:
#     :return:
#     '''
#     username = settings['USER_NAME']
#     password = settings['PASSWORD']
#     private_key = ''
#     scheme = 'file'

#     if is_relative_path:
#         url = 'http://' + url_or_relative_path
#     else:
#         url = url_or_relative_path
#     parsed_url = urlparse(url)
#     platform = parsed_url.username
#     if platform == 'nectar':
#         if 'PRIVATE_KEY_NECTAR' in settings:
#             private_key = settings['PRIVATE_KEY_NECTAR']
#         scheme = 'ssh'
#     elif platform == 'nci':
#         if 'PRIVATE_KEY_NCI' in settings:
#             private_key = settings['PRIVATE_KEY_NCI']
#         scheme = 'ssh'
#     else:
#         platform = 'local'

#     platform_object = models.Platform.objects.get(name=platform)
#     root_path = platform_object.root_path
#     if is_relative_path:
#         relative_path = parsed_url.hostname
#         url_with_pkey = '%s://%s/%s?key_filename=%s' \
#                         '&username=%s&password=%s' \
#                         '&root_path=%s' % (scheme, ip_address,
#                                            relative_path, private_key,
#                                            username, password, root_path)
#     else:
#         url_with_pkey = url_or_relative_path + \
#                         '?key_filename=%s&username=%s' \
#                         '&password=%s&root_path=%s' % (private_key,
#                                                        username, password,
#                                                        root_path)
#     logger.debug("Destination %s url_pkey %s" % (str(is_relative_path), url_with_pkey))
#     return url_with_pkey


# def multilevel_key_exists(context, *parts):
#     """
#     Returns true if context contains all parts of the key, else
#     false
#     """
#     c = dict(context)
#     for p in parts:
#         if p in c:
#             c = c[p]
#         else:
#             #logger.warn("%s not found in context" % p)
#             return False
#     return True


# def get_existing_key(context, schema):
#     """
#     Extract the schema field from the context, but if not present throw KeyError.
#     """
#     if multilevel_key_exists(context, os.path.dirname(schema), os.path.basename(schema)):
#         res = context[os.path.dirname(schema)][os.path.basename(schema)]
#     else:
#         raise KeyError("Cannot find %s in run_settings" % schema)
#     return res


# @deprecated
# def set_val(settings, k, v):
#     if not Stage.exists(settings, os.path.dirname(k)):
#             settings[os.path.dirname(k)] = {}
#     settings[os.path.dirname(k)][os.path.basename(k)] = v


class Stage(object):

    def __init__(self):
        pass

    def __init__(self, user_settings=None):
        pass

    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem.  Cannot change stage state.
        """
        return (True, "ok")
        #return (False, "All arguments are assumed invalid until verified")

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error.  SHould not change stage of stage (i.e., store any self)
        """
        # FIXME: Need to verify that triggered is idempotent.
        return True

    def process(self, context):
        """ perfrom the stage operation. Can change stage state, but not change context
        """
        pass

    def output(self, context):
        """ produce the resulting datfiles and metadata. can read stage state and change
            context
        """
        pass

    # @deprecated
    # def _exists(self, context, *parts):
    #         c = dict(context)
    #         for p in parts:
    #             if p in c:
    #                 c = c[p]
    #             else:
    #                 logger.debug("%s not found in context" % p)
    #                 return False
    #         return True


class UI(object):
    pass


# @deprecated
# class ParallelStage(Stage):
#     def triggered(self, context):
#         return True

#     def process(self, context):
#         pass

#     def output(self, context):
#         pass


@deprecated
class SequentialStage(Stage):

    def __init__(self, stages):
        self.stages = stages

    def triggered(self, context):
        return True

    def process(self, context):
        for stage in self.stages:
            if stage.triggered(context):
                stage.process(context)
                stage.output(context)

    def output(self, context):
        pass


# @deprecated
# class SmartConnector(object):
#     """ A smart Connector is a container for stages """

#     def __init__(self, stage=None):
#         self.stages = []
#         if stage:
#             self.stages.append(stage)

#     def register(self, stage):
#         self.stages.append(stage)

#     def process(self, context):
#         if self.stage.triggered(context):
#             self.stage.process(context)
#             self.stage.output(context)
#         else:
#             raise PackageFailedError()
