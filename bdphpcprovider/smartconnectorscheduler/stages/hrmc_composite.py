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
import ast
import os
import json

from bdphpcprovider.smartconnectorscheduler.stages.composite import ParallelStage
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadSpecificationError
from bdphpcprovider.smartconnectorscheduler import hrmcstages, smartconnector


logger = logging.getLogger(__name__)


class HRMCParallelStage(ParallelStage):
    """
        A list of stages
    """

    def __unicode__(self):
        return u"HRMCParallelStage"

    def get_run_map(self, settings, **kwargs):
        self.settings = settings.copy()
        try:
            rand_index = kwargs['rand_index']
        except KeyError, e:
            rand_index = 42
            logger.debug(e)
        try:
            run_settings = kwargs['run_settings']
            logger.debug(run_settings)
            smartconnector.copy_settings(self.settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
            smartconnector.copy_settings(self.settings, run_settings,
                'http://rmit.edu.au/schemas/hrmc/threshold')
            smartconnector.copy_settings(self.settings, run_settings,
                'http://rmit.edu.au/schemas/hrmc/pottype')
            smartconnector.copy_settings(self.settings, run_settings,
                'http://rmit.edu.au/schemas/hrmc/max_seed_int')
            smartconnector.copy_settings(self.settings, run_settings,
                'http://rmit.edu.au/schemas/hrmc/random_numbers')
            smartconnector.copy_settings(self.settings, run_settings,
                'http://rmit.edu.au/schemas/system/misc/id')
        except KeyError, e:
            logger.debug(e)
        logger.debug("self.settings=%s" % self.settings)
        try:
            id = self.settings['id']
            #id = smartconnector.get_existing_key(run_settings,
            #    'http://rmit.edu.au/schemas/system/misc/id')
        except KeyError, e:
            logger.error(e)
            id = 0
        logger.debug("id=%s" % id)
        # variations map spectification
        if 'pottype' in self.settings:
            logger.debug("pottype=%s" % self.settings['pottype'])
            try:
                pottype = int(self.settings['pottype'])
            except ValueError:
                logger.error("cannot convert %s to pottype" % self.settings['pottype'])
                pottype = 0
        else:
            pottype = 0

        num_dim = self.settings['number_dimensions']
        if num_dim == 1:
            N = self.settings['number_vm_instances']
            rand_nums = hrmcstages.generate_rands(self.settings,
                0, self.settings['max_seed_int'],
                N, rand_index)
            rand_index += N

            map = {
                'temp': [300],
                'iseed': rand_nums,
                'istart': [1 if id > 0 else 2],
                'pottype': [pottype]
            }
        elif num_dim == 2:
            threshold = self.settings['threshold']
            logger.debug("threshold=%s" % threshold)
            N = int(ast.literal_eval(threshold)[0])
            logger.debug("N=%s" % N)
            if not id:
                rand_nums = hrmcstages.generate_rands(
                    self.settings,
                    0, self.settings['max_seed_int'],
                    4 * N, rand_index)
                rand_index += N
                map = {
                    'temp': [300],
                    'iseed': rand_nums,
                    'istart': [2],
                    'pottype': [pottype],
                }
            else:
                rand_nums = hrmcstages.generate_rands(
                    self.settings,
                    0, self.settings['max_seed_int'],
                    1, rand_index)
                rand_index += N
                map = {
                    'temp': [i for i in [300, 700, 1100, 1500]], #Fixme: temp should be hrmc parameter
                    'iseed': rand_nums,
                    'istart': [1],
                    'pottype': [pottype],
                }
        else:
            message = "Unknown dimensionality of problem"
            logger.error(message)
            raise BadSpecificationError(message)
        logger.debug('map=%s' % map)
        return map, rand_index

    def get_total_templates(self, maps, **kwargs):
        run_settings = kwargs['run_settings']
        auth_settings = kwargs['auth_settings']
        job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']
        try:
            id = smartconnector.get_existing_key(
                run_settings, 'http://rmit.edu.au/schemas/system/misc/id')
        except KeyError, e:
            logger.error(e)
            id = 0
        iter_inputdir = os.path.join(job_dir, "input_%s" % id)
        url_with_pkey = smartconnector.get_url_with_pkey(
            auth_settings, iter_inputdir, is_relative_path=False)
        input_dirs = hrmcstages.list_dirs(url_with_pkey)
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            product = 1
            for i in map_ranges:
                product = product * len(i)
            total_templates = product * len(input_dirs)
            logger.debug("total_templates=%d" % (total_templates))
        return total_templates


def make_graph_paramset(schema_ns,
    name, graph_info, value_dict, value_keys):

    res = {}
    res['schema'] = "http://rmit.edu.au/schemas/%s" % schema_ns
    paramset = []

    def _make_param(x,y):
        param = {}
        param['name'] = x
        param['string_value'] = y
        return param

    for x, y in (
        ("graph_info", json.dumps(graph_info)),
        ("name", name),
        ('value_dict', json.dumps(value_dict)),
        ("value_keys", json.dumps(value_keys))):

        paramset.append(_make_param(x, y))
    res['parameters'] = paramset

    return res


def make_paramset(schema_ns, parameters):
    res = {}
    res['schema'] = 'http://rmit.edu.au/schemas/%s' % schema_ns
    res['parameters'] = parameters
    return res



