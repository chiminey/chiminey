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

import time
import os
import json
import utility
import logging
import logging.config
from pprint import pformat
from abc import ABCMeta, abstractmethod

from urlparse import urlparse
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler.errors import deprecated
from bdphpcprovider.smartconnectorscheduler import platform
from django.contrib import messages



logger = logging.getLogger(__name__)

class Error(Exception):
    pass


class PackageFailedError(Error):
    pass


def copy_settings(dest_context, context, key):
    """
    """
    try:
        # Note that all run_settings and user_settings are flattened
        logger.debug('context=%s' % context[os.path.dirname(key)])
        res = context[os.path.dirname(key)][os.path.basename(key)]
        dest_context[os.path.basename(key)] = res
        logger.debug("dest_contxt[%s] = %s" % (os.path.basename(key), dest_context[os.path.basename(key)]))
    except KeyError, e:
        logger.error("error on key %s" % key)
        raise

def get_platform(platform_url):
    return get_bdp_storage_url(platform_url)


def get_bdp_storage_url(platform_url):
    platform_name = platform_url.split('/')[0]
    record = platform.retrieve_platform(platform_name)
    logger.debug('record=%s' % record)
    return record
    '''
    scheme = 'ssh'
    relative_path = parsed_url.path
    host = "%s://%s%s" % (scheme, ip_address, relative_path)
    url_settings['root_path'] = root_path
    args = '&'.join(["%s=%s" % (k, v) for k, v in sorted(url_settings.items())])
    url_with_pkey = '%s://%s/%s?%s' % (scheme, ip_address,
                                           relative_path,
                                           args)
    url_with_pkey = '%s?%s' % (host, args)
    '''

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

    if '..' in url_or_relative_path:
        # .. allow url to potentially leave the user filesys. This would be bad.
        raise InvalidInputError(".. not allowed in urls")

    if is_relative_path:
        url = 'http://' + url_or_relative_path
    else:
        url = url_or_relative_path
    logger.debug("url_or_relative_path=%s" % url_or_relative_path)
    parsed_url = urlparse(url)
    platform = parsed_url.username
    url_settings = {}
    if platform == 'nectar':
        url_settings['username'] = settings['username']
        #url_settings['password'] = settings['nectar_password']
        url_settings['key_file'] = settings['private_key']
        # key_file = settings['nectar_private_key']
        # username = settings['nectar_username']
        # password = settings['nectar_password']
        url_settings['root_path'] = settings['root_path']
        args = '&'.join(["%s=%s" % (k, v) for k, v in sorted(url_settings.items())])
        scheme = 'ssh'

    elif platform == 'nci':
        url_settings['username'] = settings['nci_user']
        url_settings['password'] = settings['nci_password']
        url_settings['key_file'] = settings['nci_private_key']
        # key_file = settings['nci_private_key']
        # username = settings['nci_user']
        # password = settings['nci_password']

        scheme = 'ssh'
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
    try:
        platform_object = models.Platform.objects.get(name=platform)
    except models.Platform.DoesNotExist:
        logger.error('compatible platform for %s not found' % platform)

    # FIXME: suffix root_path with username
    if platform != 'nectar':
        root_path = platform_object.root_path
        url_settings['root_path'] = root_path
    # FIXME: URIs cannot contain unicode data, but IRI can. So need to convert IRI to URL
    # if parameters can be non-ascii
    # https://docs.djangoproject.com/en/dev/ref/unicode/#uri-and-iri-handling
    args = '&'.join(["%s=%s" % (k, v) for k, v in sorted(url_settings.items())])
    if is_relative_path:
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
    logger.debug("Destination %s url_pkey %s" % (str(is_relative_path), url_with_pkey))
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


def multilevel_key_exists(context, *parts):
    """
    Returns true if context contains all parts of the key, else
    false
    """
    c = dict(context)
    for p in parts:
        if p in c:
            c = c[p]
        else:
            #logger.warn("%s not found in context" % p)
            return False
    return True

def get_existing_key(context, schema):
    """
    Extract the schema field from the context, but if not present throw KeyError.
    """
    if multilevel_key_exists(context, os.path.dirname(schema), os.path.basename(schema)):
        res = context[os.path.dirname(schema)][os.path.basename(schema)]
    else:
        raise KeyError()
    return res


@deprecated
def set_val(settings, k, v):
    if not Stage.exists(settings, os.path.dirname(k)):
            settings[os.path.dirname(k)] = {}
    settings[os.path.dirname(k)][os.path.basename(k)] = v


class Stage(object):

    def __init__(self):
        pass

    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem
        """
        return (True, "ok")
        #return (False, "All arguments are assumed invalid until verified")

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that triggered is idempotent.
        return True

    def process(self, context):
        """ perfrom the stage operation
        """
        pass

    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        pass

    @deprecated
    def _exists(self, context, *parts):
            c = dict(context)
            for p in parts:
                if p in c:
                    c = c[p]
                else:
                    logger.warn("%s not found in context" % p)
                    return False
            return True


def addMessage(run_settings, level, msg):
    try:
        context_id = get_existing_key(run_settings,
            "http://rmit.edu.au/schemas/system/contextid")
    except KeyError:
        logger.error("unable to load contextid from run_settings")
        logger.error(pformat(run_settings))
        return
    logger.debug("context_id=%s" % context_id)
    if not context_id:
        logger.error("invalid context_id")
        return
    mess = '%s,%s' % (level, msg)
    logger.debug("mess=%s" % mess)
    from bdphpcprovider.smartconnectorscheduler import tasks
    tasks.context_message.delay(context_id, mess)


def debug(run_settings, msg):
    return addMessage(run_settings, 'debug', msg)


def info(run_settings, msg):
    return addMessage(run_settings, 'info', msg)


def success(run_settings, msg):
    return addMessage(run_settings, 'success', msg)


def warn(run_settings, msg):
    return addMessage(run_settings, 'warning', msg)


def error(run_settings, msg):
    return addMessage(run_settings, 'error', msg)


class UI(object):
    pass


# class Configure(Stage, UI):
#     """
#         - Load config.sys file into the filesystem
#         - Nothing beyond specifying the path to config.sys
#         - Later could be dialogue box,...

#     """
#     def triggered(self, context):
#         #check for filesystem in context
#         return True

#         #logger.debug("%s" % field_val)
#     def process(self, context):
#         # - Load config.sys file into the filesystem
#         # - Nothing beyond specifying the path to config.sys
#         # - Later could be dialogue box,...
#         # 1. creates instance of file system
#         # 2. pass the file system as entry in the Context
#         # create status  file in file system
#         #print " Security Group", filesystem.settings.SECURITY_GROUP

#         pass

#     # indicate the process() is completed
#     def output(self, context):
#         # store in filesystem
#         pass


# class Create(Stage):
#     def triggered(self, context):
#         """ return true if the directory pattern triggers this stage
#         """
#         #check the context for existence of a file system or other
#         # key words, then if true, trigger
#         #self.metadata = self._load_metadata_file()

#         if True:
#             self.boto_settings = utility.load_generic_settings()
#             return True

#     def _transform_the_filesystem(filesystem, settings):
#         key = settings['ec2_access_key']
#         print key

#     def process(self, context):

#         # get the input from the user to override config settings
#         # load up the metadata

#         #settings = {}
#         #settings['number_vm_instances'] = self.metadata.number

#         #settings['ec2_access_key'] = self.metadata.ec2_access_key
#         #settings['ec2_secret_key'] = self.metadata.ec2_secret_key
#         # ...

#         #self.temp_sys = FileSystem(filesystem)

#         #self._transform_the_filesystem(self.temp_sys, settings)

#         #import codecs
#         #f = codecs.open('metadata.json', encoding='utf-8')
#         #import json
#         #metadata = json.loads(f.read())
#         print "Security Group ", self.boto_settings.SECURITY_GROUP
#         pass

#     def output(self, context):
#         # store in filesystem
#         #self._store(self.temp_sys, filesystem)
#         pass


# class Setup(Stage):

#     def triggered(self, context):
#         pass

#     def process(self, context):
#         pass

#     def output(self, context):
#         pass


# class Run(Stage):
#     #json output
#     def triggered(self, context):
#         pass

#     def process(self, context):
#         pass

#     def output(self, context):
#         pass


# class Check(Stage):
#     def triggered(self, context):
#         pass

#     def process(self, context):
#         pass

#     def output(self, context):
#         pass


# class Teardown(Stage):
#     def triggered(self, context):
#         pass

#     def process(self, context):
#         pass

#     def output(self, context):
#         pass


class ParallelStage(Stage):
    def triggered(self, context):
        return True

    def process(self, context):

        while(True):
            done = 0
            for stage in smart_con.stages:
                print "Working in stage", stage
                if stage.triggered(context):
                    stage.process(context)
                    stage.output(context)
                    done += 1
                    #smart_con.unregister(stage)
                    #print "Deleting stage",stage
                    print done
            if done == len(smart_con.stages):
                break

        while s.triggered(context):
            s.process(context)
            s.output(context)
            print context

    def output(self, context):
        pass


class GridParameterStage(Stage):
    pass


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


class SmartConnector(object):
    """ A smart Connector is a container for stages """

    def __init__(self, stage=None):
        self.stages = []
        if stage:
            self.stages.append(stage)

    def register(self, stage):
        self.stages.append(stage)

    def process(self, context):
        if self.stage.triggered(context):
            self.stage.process(context)
            self.stage.output(context)
        else:
            raise PackageFailedError()


# def mainloop():
# # load system wide settings, e.g Security_Group
# #communicating between stages: crud context or filesystem
# #build context with file system as its only entry
#     context = {}
#     context['version'] = "1.0.0"

#     #smart_con = SmartConnector()
#     filesys = FileSystem()
#     path_fs = '/home/iyusuf/connectorFS'
#     filesys.create_initial_filesystem(path_fs)
#    # filesys.create_file(path_fs, 'Iman')
#     filesys.create_filesystem("newFS")

#     filesys.delete_filesystem("newFS")
#     filesys.delete_file("Iman")
#     filesys.create_file('/home/iyusuf/Butini',
#                         dest_filesystem='/home/iyusuf/connectorFS/Seid')

#     file_name = 'tobeupdated'
#     absolute_path = os.path.join(filesys.toplevel_filesystem,
#                                  file_name)

#     f = open(absolute_path, 'w')
#     f.write("Line 1")
#     f.write("line 2")
#     f.close()


#     #filesys.update_file('Butini')
#     #filesys.delete_file(path_fs, 'Iman')

#     #filesys.create_initial_filesystem()
#     #filesys.load_generic_settings()

#     #for stage in (Configure(), Create(), Setup(), Run(), Check(), Teardown()):
#      #   smart_con.register(stage)


#     #print smart_con.stages

#     #while loop is infinite:
#     # check the semantics for 'dropping data' into
#     # designated location.
#     #What happens if data is dropped while
#     #another is in progress?


#     #while(True):

#     #while (True):
#      #   done = 0
#       #  for stage in smart_con.stages:
#        #     print "Working in stage",stage
#         #    if stage.triggered(context):
#          #       stage.process(context)
#           #      stage.output(context)
#            #     done += 1
#                 #smart_con.unregister(stage)
#                 #print "Deleting stage",stage
#             #    print done

#         #if done == len(smart_con.stages):
#          #   break

# if __name__ == '__main__':
#     begins = time.time()
#     mainloop()
#     ends = time.time()
#     print "Total execution time: %d seconds" % (ends - begins)
