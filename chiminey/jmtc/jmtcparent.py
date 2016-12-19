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

import ast
import logging
import ast
import os
from itertools import product
from chiminey.corestages.parent import Parent
from chiminey.smartconnectorscheduler.errors import BadSpecificationError
from chiminey.smartconnectorscheduler import jobs
from chiminey.runsettings import update, getval, getvals, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_all_files, get_basename, list_dirs
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class JmtcParent(Parent):
    """
        A list of corestages
    """
    def __init__(self, user_settings=None):
        logger.debug("JmtcParallelStage")
        pass

    def is_triggered(self, context):
        return False

    def __unicode__(self):
        return u"JmtcParallelStage"

    def get_internal_sweep_map(self, settings, **kwargs):
        run_settings = kwargs['run_settings']
        rand_index = 42
        additional_sweep_parameters = {}
        additional_map = {}
        jmtconnector_model_file = ''
        jmtconnector_jmt_tool = ''
        jmtconnector_jsim_seed = 0
        jmtconnector_jsim_maxtime = 0

        if '%s/input/jmtc' % django_settings.SCHEMA_PREFIX in run_settings:
            try:
                jmtconnector_model_file = getval(run_settings, '%s/input/jmtc/jmtconnector_model_file' % django_settings.SCHEMA_PREFIX)
                logger.debug("jmtconnector_model_file=%s" % jmtconnector_model_file)
            except ValueError:
                logger.error("cannot convert %s to jmtconnector_model_file" % getval(run_settings, '%s/input/jmtc/jmtconnector_model_file' % django_settings.SCHEMA_PREFIX))
            try:
                jmtconnector_jmt_tool = getval(run_settings, '%s/input/jmtc/jmtconnector_jmt_tool' % django_settings.SCHEMA_PREFIX)
                logger.debug("jmtconnector_jmt_tool=%s" % jmtconnector_jmt_tool)
            except ValueError:
                logger.error("cannot convert %s to jmtconnector_jmt_tool" % getval(run_settings, '%s/input/jmtc/jmtconnector_jmt_tool' % django_settings.SCHEMA_PREFIX))
            try:
                jmtconnector_jsim_seed = getval(run_settings, '%s/input/jmtc/jmtconnector_jsim_seed' % django_settings.SCHEMA_PREFIX)
                logger.debug("jmtconnector_jsim_seed=%s" % jmtconnector_jsim_seed)
            except ValueError:
                logger.error("cannot convert %s to jmtconnector_jsim_seed" % getval(run_settings, '%s/input/jmtc/jmtconnector_jsim_seed' % django_settings.SCHEMA_PREFIX))
            try:
                jmtconnector_jsim_maxtime = getval(run_settings, '%s/input/jmtc/jmtconnector_jsim_maxtime' % django_settings.SCHEMA_PREFIX)
                logger.debug("jmtconnector_jsim_maxtime=%s" % jmtconnector_jsim_maxtime)
            except ValueError:
                logger.error("cannot convert %s to jmtconnector_jsim_maxtime" % getval(run_settings, '%s/input/jmtc/jmtconnector_jsim_maxtime' % django_settings.SCHEMA_PREFIX))

            try:
                additional_sweep_parameters = getval(run_settings, '%s/input/jmtc/additional_sweep_parameters' % django_settings.SCHEMA_PREFIX)
                logger.debug("additional_sweep_parameters=%s" % additional_sweep_parameters)
            except ValueError:
                logger.error("cannot convert %s to additional_sweep_parameters" % getval(run_settings, '%s/input/jmtc/additional_sweep_parameters' % django_settings.SCHEMA_PREFIX))
            map = {
                'jmtconnector_model_file': [jmtconnector_model_file],
                'jmtconnector_jmt_tool': [jmtconnector_jmt_tool],
                'jmtconnector_jsim_seed': [jmtconnector_jsim_seed],
                'jmtconnector_jsim_maxtime': [jmtconnector_jsim_maxtime] 
            }

            try:
                additional_map = dict(ast.literal_eval(additional_sweep_parameters))
            except e:
                logger.debug(e)
                raise BadSpecificationError(e)

            if additional_map:
                for key in additional_map:
                    map[key] = additional_map[key] 
        else:
            message = "Unknown dimensionality of problem"
            logger.error(message)
            raise BadSpecificationError(message)
        
        logger.debug('map=%s' % map)
        return map, rand_index
