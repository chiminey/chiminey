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


class RAC3DParent(Parent):
    """
        A list of corestages
    """
    def __init__(self, user_settings=None):
        logger.debug("RAC3DParallelStage")
        pass

    def is_triggered(self, context):
        return False

    def __unicode__(self):
        return u"RAC3DParallelStage"

    def get_internal_sweep_map(self, settings, **kwargs):
        run_settings = kwargs['run_settings']
        logger.debug('run_settings=%s' % run_settings)
        rand_index = 42

        if '%s/input/3drac' % django_settings.SCHEMA_PREFIX in run_settings:
            try:
                self.datafile = getval(run_settings, '%s/input/3drac/data_file_name' % django_settings.SCHEMA_PREFIX)
                logger.debug('Data file name =%s' % self.datafile)
            except ValueError:
                logger.error("cannot convert %s to data file name" % getval(run_settings, '%s/input/3drac/data_file_name' % django_settings.SCHEMA_PREFIX))

            try: 
                virtual_blocks = getval(run_settings, '%s/input/3drac/virtual_blocks_list' % django_settings.SCHEMA_PREFIX)
                self.b_list = ast.literal_eval(virtual_blocks)
                logger.debug('Valid blocks list =%s' % str(self.b_list))
            except ValueError:
                logger.error("cannot convert %s to valid blocks list %s" % getval(run_settings, '%s/input/3drac/virtual_blocks_list' % django_settings.SCHEMA_PREFIX))
          
            map = {
                'data_file_name': [self.datafile],
                'virtual_blocks_list': self.b_list,
            }
        else:
            message = "Unknown dimensionality of problem"
            logger.error(message)
            raise BadSpecificationError(message)
        
        logger.debug('map=%s' % map)
        return map, rand_index
