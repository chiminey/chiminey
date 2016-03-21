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
import os
from itertools import product
from chiminey.runsettings import getval, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs
from chiminey.corestages.stage import Stage
from django.conf import settings as django_settings


logger = logging.getLogger(__name__)


class Parent(Stage):
    """
        A list of corestages
    """
    def __init__(self, user_settings=None):
        logger.debug("ps__init")
        pass

    def __unicode__(self):
        return u"ParallelStage"

    def is_triggered(self, run_settings):
        '''
        logger.debug("Parallel Stage Triggered")
        logger.debug("run_settings=%s" % run_settings)

        if self._exists(run_settings, u'http://rmit.edu.au/schemas/stages/parallel/testing',
            u'output'):
            self.val = run_settings[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'output']
        else:
            self.val = 0

        if self._exists(run_settings, u'http://rmit.edu.au/schemas/stages/parallel/testing',
            u'index'):
            self.parallel_index = run_settings[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'index']
        else:
            try:
                self.parallel_index = run_settings[u'http://rmit.edu.au/schemas/smartconnector1/create'][u'parallel_number']
            except KeyError:
                logger.error("run_settings=%s" % run_settings)
                raise

        if self.parallel_index:
            return True
        '''
        return False

    def process(self, run_settings):
        logger.debug("Parallel Stage Processing")
        pass

    def output(self, run_settings):
        logger.debug("Parallel Stage Output")

        if not self._exists(run_settings, u'http://rmit.edu.au/schemas/stages/parallel/testing'):
            run_settings[u'http://rmit.edu.au/schemas/stages/parallel/testing'] = {}

        self.val += 1
        run_settings[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'output'] = self.val

        self.parallel_index -= 1
        run_settings[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'index'] = self.parallel_index
        return run_settings

    def get_internal_sweep_map(self, settings, **kwargs):
        rand_index = 42
        map = {'val': [1]}
        logger.debug('map=%s' % map)
        return map, rand_index

    def get_total_procs_per_iteration(self, maps, **kwargs):
        try:
            run_settings = kwargs['run_settings']
            input_exists = self.input_exists(run_settings)
        except KeyError:
            input_exists = False
        if input_exists:
            return self._get_procs_from_input_dirs(maps, **kwargs)
        else:
            return self._get_procs_from_map_variations(maps)

    def _get_procs_from_input_dirs(self, maps, **kwargs):
        run_settings = kwargs['run_settings']
        output_storage_settings = kwargs['output_storage_settings']
        job_dir = kwargs['job_dir']

        try:
            id = getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException as e:
            logger.error(e)
            id = 0
        iter_inputdir = os.path.join(job_dir, "input_%s" % id)
        url_with_pkey = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                           output_storage_settings['type'],
                            iter_inputdir),
            is_relative_path=False)
        logger.debug(url_with_pkey)
        input_dirs = list_dirs(url_with_pkey)
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            product = 1
            for i in map_ranges:
                product = product * len(i)
            total_procs = product * len(input_dirs)
            logger.debug("total_procs=%d" % (total_procs))
        return total_procs

    def _get_procs_from_map_variations(self, maps):
        contexts = []
        num_variations = 0
        for run_map in maps:
            logger.debug("run_map=%s" % run_map)
            map_keys = run_map.keys()
            map_ranges = [list(run_map[x]) for x in map_keys]
            logger.debug("map_ranges=%s" % map_ranges)
            for z in product(*map_ranges):
                context = {}
                for i, k in enumerate(map_keys):
                    context[k] = str(z[i])  # str() so that 0 doesn't default value
                contexts.append(context)
                num_variations += 1
        logger.debug("num_variations=%s" % num_variations)
        return num_variations