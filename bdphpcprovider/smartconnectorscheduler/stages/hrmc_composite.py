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
        except KeyError, e:
            logger.debug(e)
        try:
            self.id = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/system/misc/id')
        except KeyError, e:
            self.id = 0
        # variations map spectification
        if 'pottype' in self.settings:
            logger.debug("pottype=%s" % self.settings['pottype'])
            try:
                pottype = int(self.settings['pottype'])
            except ValueError:
                logger.error("cannot convert %s to pottype" %self.settings['pottype'])
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
                'istart': [1 if self.id > 0 else 2],
                'pottype': [pottype]
            }
        elif num_dim == 2:
            self.threshold = self.settings['threshold']
            logger.debug("threshold=%s" % self.threshold)
            N = int(ast.literal_eval(self.threshold)[0])
            logger.debug("N=%s" % N)
            if not self.id:
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
                    1, self.rand_index)
                self.rand_index += N
                map = {
                    'temp': [i for i in [300, 700, 1100, 1500]],
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