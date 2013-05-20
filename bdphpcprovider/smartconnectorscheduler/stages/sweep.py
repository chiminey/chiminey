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

import sys
import os
import ast
import time
import logging
import logging.config
import json
import re
import tempfile
from itertools import product
from pprint import pformat
from urlparse import urlparse, parse_qsl

from django.template import Context, Template

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import botocloudconnector
from bdphpcprovider.smartconnectorscheduler.errors import PackageFailedError
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import deprecated
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadSpecificationError, BadInputException
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


class Sweep(Stage):
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        self.numbfile = 0

        self.job_dir = "hrmcrun"
        self.boto_settings = user_settings.copy()
        logger.debug("Run stage initialized")

    def triggered(self, run_settings):
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/sweep',
            'sweep_done'):
            configure_done = int(run_settings['http://rmit.edu.au/schemas/stages/sweep'][u'sweep_done'])
            return not configure_done
        return True

    def _expand_variations(self, maps, values):
        """
        Based on maps, generate all range variations from the template
        """
        # FIXME: doesn't handle multipe template files together
        res = []
        numbfile = 0
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            logger.debug("iter #%d" % iter)
            # ensure ordering of the template_map entries
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            logger.debug("map_ranges=%s"  % map_ranges)
            for z in product(*map_ranges):
                logger.debug("len(z)=%s" % len(z))
                context = dict(values)
                for i, k in enumerate(map_keys):

                    logger.debug("i=%s k=%s" % (i, k))
                    logger.debug("z[i]=%s" % z[i])
                    context[k] = str(z[i])  # str() so that 0 doesn't default value
                    #logger.debug("context[%s] = %s" % (k, context[k]))
                context['run_counter'] = numbfile
                numbfile += 1
                res.append(context)
        return res

    def process(self, run_settings):

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/pottype')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/error_threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/max_iteration')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/random_numbers')

        contextid = int(run_settings['http://rmit.edu.au/schemas/system'][u'contextid'])
        logger.debug("contextid=%s" % contextid)

        self.rand_index = run_settings['http://rmit.edu.au/schemas/hrmc']['iseed']
        logger.debug("rand_index=%s" % self.rand_index)

        context = models.Context.objects.get(id=contextid)
        user = context.owner.user.username
        self.job_dir = run_settings['http://rmit.edu.au/schemas/system/misc'][u'output_location']

        # generate all variations
        map = {
            'var1': [3, 7],
            'var2': [1, 2]
        }
        runs = self._expand_variations(maps=[map], values={})

        # prep random seeds for each run based off original iseed
        # FIXME: inefficient for large random file
        # TODO, FIXME: this is potentially problematic if different
        # runs end up overlapping in the random numbers they utilise.
        # solution is to have separate random files per run or partition
        # big file up.
        rands = hrmcstages.generate_rands(settings=self.boto_settings,
            start_range=0,
            end_range=-1,
            num_required=len(runs),
            start_index=self.rand_index)

        logger.debug("rands=%s" % rands)
        logger.debug("runs=%s" % runs)

        # For each of the generated runs, copy across and modify input directory
        # and then schedule subrun of hrmc connector
        for i, run in enumerate(runs):
            # Duplicate input directory into runX duplicates

            logger.debug("run=%s" % run)
            logger.debug("run_settings=%s" % run_settings)
            run_counter = int(run['run_counter'])
            logger.debug("run_counter=%s" % run_counter)
            input_location = run_settings['http://rmit.edu.au/schemas/stages/sweep'][u'input_location']
            input_url = smartconnector.get_url_with_pkey(self.boto_settings,
                input_location)
            logger.debug("input_url=%s" % input_url)
            # job_dir contains some overriding context that this run is situated under
            run_inputdir = os.path.join(self.job_dir,
                "run%s" % str(run_counter),
                "input_0", "initial")
            logger.debug("run_inputdir=%s" % run_inputdir)
            run_iter_url = smartconnector.get_url_with_pkey(self.boto_settings,
                run_inputdir, is_relative_path=True)
            logger.debug("run_iter_url=%s" % run_iter_url)
            hrmcstages.copy_directories(input_url, run_iter_url)

            # Q: copy payload_location to gridYY/payload_Z ? this would allow templating of this too????
            # TODO: can we have multiple values files per input_dir or just one.
            # if mulitple, then need template_name(s).  Otherwise, run stage templates
            # all need to refer to same value file...
            template_name = run_settings['http://rmit.edu.au/schemas/stages/sweep'][u'template_name']
            logger.debug("template_name=%s" % template_name)

            # Need to load up existing values, because original input_dir could
            # have contained values for the whole run
            run_counter = int(run['run_counter'])
            run_inputdir = os.path.join(self.job_dir,
                "run%s" % run_counter,
                "input_0")
            values_map = {}
            try:
                values_url = smartconnector.get_url_with_pkey(
                    self.boto_settings,
                    os.path.join(run_inputdir, "initial",
                        '%s_values' % template_name),
                    is_relative_path=True)

                logger.debug("values_url=%s" % values_url)
                values_content = hrmcstages.get_file(values_url)
                logger.debug("values_content=%s" % values_content)
                values_map = dict(json.loads(values_content))
            except IOError:
                logger.warn("no values file found")
            # include run variations into the values_map
            values_map.update(run)
            logger.debug("new values_map=%s" % values_map)
            hrmcstages.put_file(values_url, json.dumps(values_map))

            # make run_context for hrmc with input_location pointing at runX
            # and outputinto to suffix from job_dir (which will be given
            #  contextid suffix)

            system_dict = {
            u'system': u'settings',
            u'output_location': os.path.join(self.job_dir, 'hrmcrun')}

            system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

            platform = "nectar"
            directive_name = "smartconnector_hrmc"
            directive_args = []

            run_inputdir = os.path.join(self.job_dir,
                "run%s" % str(run_counter),
                "input_0", "initial")

            new_input_location = "file://127.0.0.1/%s/run%s/input_0" % (self.job_dir, run_counter)

            directive_args.append(
                ['',
                    ['http://rmit.edu.au/schemas/hrmc',
                        ('number_vm_instances', self.boto_settings['number_vm_instances']),
                        (u'iseed', rands[i]),
                        ('input_location',  new_input_location),
                        ('number_dimensions', self.boto_settings['number_dimensions']),
                        ('threshold', self.boto_settings['threshold']),
                        ('error_threshold', self.boto_settings['error_threshold']),
                        ('max_iteration', self.boto_settings['max_iteration']),
                        ('pottype', self.boto_settings['pottype'])
                    ]
                ])

            logger.debug("directive_name=%s" % directive_name)
            logger.debug("directive_args=%s" % directive_args)
            try:
                (task_run_settings, command_args, run_context) \
                    = hrmcstages.make_runcontext_for_directive(
                    platform,
                    directive_name,
                    directive_args, system_settings, user)

            except InvalidInputError, e:
                logger.error(str(e))
        logger.debug("sweep process done")

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/sweep',
            {})[u'sweep_done'] = 1
        return run_settings
