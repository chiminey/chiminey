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


import logging
from bdphpcprovider.corestages.stage import Stage


logger = logging.getLogger(__name__)


class ParallelStage(Stage):
    """
        A list of corestages
    """
    def __init__(self, user_settings=None):
        logger.debug("ps__init")
        pass

    def __unicode__(self):
        return u"ParallelStage"

    def triggered(self, run_settings):
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


    def get_run_map(self, settings, **kwargs):
        return {}, kwargs

    def get_total_templates(self, maps, **kwargs):
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            total_templates = 0
            # ensure ordering of the template_map entries
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            product = 1
            for i in map_ranges:
                product = product * len(i)
            total_templates = product
            #for z in product(*map_ranges):
            #    total_templates += 1
            logger.debug("total_templates=%d" % (total_templates))
        return total_templates




