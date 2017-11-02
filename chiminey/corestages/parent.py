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
        return False

    def process(self, run_settings):
        logger.debug("Parallel Stage Processing")
        pass

    def output(self, run_settings):
        logger.debug("Parallel Stage Output")

        if not self._exists(run_settings, u'%s/stages/parallel/testing' % django_settings.SCHEMA_PREFIX):
            run_settings[u'%s/stages/parallel/testing' % django_settings.SCHEMA_PREFIX] = {}

        self.val += 1
        run_settings[u'%s/stages/parallel/testing' % django_settings.SCHEMA_PREFIX][u'output'] = self.val

        self.parallel_index -= 1
        run_settings[u'%s/stages/parallel/testing' % django_settings.SCHEMA_PREFIX][u'index'] = self.parallel_index
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

        maps_size = len(maps)
        logger.debug("ZZZZ maps: %s" % (maps))
        logger.debug("ZZZZ len(maps): %d" % (maps_size))
        if maps_size > 1:
            iter_total_procs=0
            logger.debug("ZZZZ>1 inside loop")
            for xx in range(maps_size): 
                temp_maps = [maps[xx]]
                for iter, template_map in enumerate(temp_maps):
                    logger.debug("ZZZZ>1 template_map=%s" % template_map)
                    map_keys = template_map.keys()
                    logger.debug("ZZZZ>1 map_keys %s" % map_keys)
                    map_ranges = [list(template_map[x]) for x in map_keys]
                    product = 1
                    for i in map_ranges:
                        product = product * len(i)
                    total_procs = product * len(input_dirs)
                iter_total_procs=iter_total_procs + total_procs 
            total_procs=iter_total_procs
            logger.debug("ZZZZ>1 total_procs=%d" % (total_procs))
        else:
            for iter, template_map in enumerate(maps):
                logger.debug("ZZZZ<1 template_map=%s" % template_map)
                map_keys = template_map.keys()
                logger.debug("ZZZZ<1 map_keys %s" % map_keys)
                map_ranges = [list(template_map[x]) for x in map_keys]
                product = 1
                for i in map_ranges:
                    product = product * len(i)
                total_procs = product * len(input_dirs)
                logger.debug("ZZZZ<1 total_procs=%d" % (total_procs))
        return total_procs

    def _get_procs_from_map_variations(self, maps):
        contexts = []
        num_variations = 0

        maps_size = len(maps)

        logger.debug("YYYY maps: %s" % (maps))
        logger.debug("YYYY len(maps): %d" % (maps_size))

        if maps_size > 1:
            logger.debug("YYYY>1 inside loop")
            for xx in range(maps_size): 
                temp_maps = [maps[xx]]
                for run_map in temp_maps:
                    logger.debug("YYYY>1 run_map=%s" % run_map)
                    map_keys = run_map.keys()
                    map_ranges = [list(run_map[x]) for x in map_keys]
                    logger.debug("YYYY>1 map_ranges=%s" % map_ranges)
                    for z in product(*map_ranges):
                        context = {}
                        for i, k in enumerate(map_keys):
                            context[k] = str(z[i])  # str() so that 0 doesn't default value
                        contexts.append(context)
                        num_variations += 1
                xx=xx-1
        else:
            logger.debug("YYYY<=1 inside loop")
            for run_map in maps:
                logger.debug("YYYY<=1 run_map=%s" % run_map)
                map_keys = run_map.keys()
                map_ranges = [list(run_map[x]) for x in map_keys]
                logger.debug("YYYY<=1 map_ranges=%s" % map_ranges)
                for z in product(*map_ranges):
                    context = {}
                    for i, k in enumerate(map_keys):
                        context[k] = str(z[i])  # str() so that 0 doesn't default value
                    contexts.append(context)
                    num_variations += 1
        logger.debug("YYYY num_variations=%s" % num_variations)
        return num_variations
