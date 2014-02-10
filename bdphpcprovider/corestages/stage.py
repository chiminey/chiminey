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
from bdphpcprovider.platform import get_platform_settings
from bdphpcprovider.runsettings import getval, setvals, SettingNotFoundException

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


logger = logging.getLogger(__name__)


class Stage(object):
    def __init__(self):
        pass

    def __init__(self, user_settings=None):
        pass


    def input_valid(self, settings_to_test):
        """ Return a tuple, where the first element is True settings_to_test
        are syntactically and semantically valid for this stage.  Otherwise,
        return False with the second element in the tuple describing the
        problem
        """
        return (True, "ok")
        #return (False, "All arguments are assumed invalid until verified")

    def is_triggered(self, run_settings):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that is_triggered is idempotent.
        return True

    def process(self, run_settings):
        """ perfrom the stage operation
        """
        pass

    def output(self, run_settings):
        """ produce the resulting datfiles and metadata
        """
        pass

    def get_platform_settings(self, run_settings, namespace_prefix):
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        platform_url = run_settings[namespace_prefix]['platform_url']
        return get_platform_settings(platform_url, bdp_username)


    def set_stage_settings(self, run_settings, local_settings):
        pass

    def set_domain_settings(self, run_settings, local_settings):
        pass

    def input_exists(self, run_settings):
        try:
            getval(run_settings, 'http://rmit.edu.au/schemas/input/location/input/input_location')
            return True
        except SettingNotFoundException:
            pass
        try:
            getval(run_settings, 'http://rmit.edu.au/schemas/input/system/input_location')
            return True
        except SettingNotFoundException:
            pass
        return False


    def output_exists(self, run_settings):
        try:
            getval(run_settings, 'http://rmit.edu.au/schemas/input/location/output/output_location')
            return True
        except SettingNotFoundException:
            pass
        try:
            getval(run_settings, 'http://rmit.edu.au/schemas/input/system/output_location')
            return True
        except SettingNotFoundException:
            pass
        return False


    @deprecated
    def _exists(self, context, *parts):
            c = dict(context)
            for p in parts:
                if p in c:
                    c = c[p]
                else:
                    logger.debug("%s not found in context" % p)
                    return False
            return True


    def break_bdp_url(self, bdpurl):

        bdpurl_list = bdpurl.split('/')
        platform_name = bdpurl_list[0]
        offset = ''
        if len(bdpurl_list) > 1:
            offset = os.path.join(*bdpurl_list[1:])
        logger.debug('platform_name=%s, bdpurl_offset=%s' % (platform_name, offset))
        return platform_name, offset


    def get_process_output_path(self, run_settings, process_id):
        computation_platform = self.get_platform_settings(
            run_settings, 'http://rmit.edu.au/schemas/platform/computation')
        output_path = os.path.join(
                computation_platform['root_path'],
                getval(run_settings, 'http://rmit.edu.au/schemas/stages/setup/payload_destination'),
                str(process_id), getval(run_settings, 'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname'))
        return output_path

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


def get_bdp_storage_url(platform_url, username):
    platform_name = platform_url.split('/')[0]
    record, namespace = retrieve_platform(platform_name, username)
    logger.debug('record=%s' % record)
    return record, namespace





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

class UI(object):
    pass
