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
from bdphpcprovider.smartconnectorscheduler import models, platform, storage


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Sweep(Stage):

    # hrmc_schema = "http://rmit.edu.au/schemas/hrmc/"
    # system_schema = "http://rmit.edu.au/schemas/system/misc/"
    # sweep_schema = 'http://rmit.edu.au/schemas/stages/sweep/'

    def __init__(self, user_settings=None):
        self.numbfile = 0

        self.job_dir = "hrmcrun"
        logger.debug("Sweep stage initialized")

    def triggered(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/sweep',
            'sweep_done'):
            configure_done = int(run_settings['http://rmit.edu.au/schemas/stages/sweep'][u'sweep_done'])
            return not configure_done
        return True

    #def generalise_platform_parameters(self, generic_schema, current_schema):
    #    for k, v in current

    def process(self, run_settings):

        # Need to make copy because we pass on run_settings to sub connector
        # so any changes we make to run_settings will be inherited

        logger.debug('run_settings=%s' % run_settings)
        from copy import deepcopy
        local_settings = deepcopy(run_settings[models.UserProfile.PROFILE_SCHEMA_NS])

        smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/input/mytardis/experiment_id')
        smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/system/random_numbers')

        logger.debug('local_settings=%s' % local_settings)

        contextid = int(run_settings['http://rmit.edu.au/schemas/system'][
            u'contextid'])
        logger.debug("contextid=%s" % contextid)

        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/system',
            'parent_contextid'):
            parent_contextid = int(run_settings['http://rmit.edu.au/schemas/system'][u'parent_contextid'])
        else:
            parent_contextid = 0

        computation_platform_name = run_settings['http://rmit.edu.au/schemas/input/system/compplatform']['computation_platform']
        run_settings[RMIT_SCHEMA + '/platform/computation'] = {}
        run_settings[RMIT_SCHEMA + '/platform/computation']['platform_url'] = computation_platform_name

        output_location = run_settings['http://rmit.edu.au/schemas/input/system'][u'output_location']
        output_location_list = output_location.split('/')
        output_storage_name = output_location_list[0]
        output_storage_offset = ''
        if len(output_location_list) > 1:
            output_storage_offset = os.path.join(*output_location_list[1:])
        logger.debug('output_storage_offset=%s' % output_storage_offset)

        run_settings[RMIT_SCHEMA + '/platform/storage/output'] = {}
        run_settings[RMIT_SCHEMA + '/platform/storage/output']['platform_url'] = output_storage_name
        run_settings['http://rmit.edu.au/schemas/platform/storage/output']['offset'] = \
            os.path.join(output_storage_offset, 'sweep%s' % contextid)


        minput_location = run_settings['http://rmit.edu.au/schemas/input/system'][u'input_location']
        input_location_list = minput_location.split('/')
        input_storage_name = input_location_list[0]
        input_storage_offset = ''
        if len(input_location_list) > 1:
            input_storage_offset = os.path.join(*input_location_list[1:])
        logger.debug('input_storage_offset=%s' % input_storage_offset)

        run_settings[RMIT_SCHEMA + '/platform/storage/input'] = {}
        run_settings[RMIT_SCHEMA + '/platform/storage/input']['platform_url'] = input_storage_name
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        input_storage_url = run_settings['http://rmit.edu.au/schemas/platform/storage/input']['platform_url']
        input_storage_settings = platform.get_platform_settings(input_storage_url, bdp_username)
        run_settings['http://rmit.edu.au/schemas/platform/storage/input']['offset'] = input_storage_offset


        # TODO: move iseed out of hrmc into separate schema to use on any
        # sweepable connector and make this function completely hrmc independent.


        context = models.Context.objects.get(id=contextid)
        user = context.owner.user.username
        #self.job_dir = run_settings['http://rmit.edu.au/schemas/input/system'][
        #    u'output_location']
        self.job_dir = 'file://local@127.0.0.1/sweep%s' % contextid #todo replace with scratch space

        subdirective = run_settings['http://rmit.edu.au/schemas/stages/sweep']['directive']
        subdirective_ns = "http://rmit.edu.au/schemas/input/%s" % subdirective

        map_text = run_settings['http://rmit.edu.au/schemas/input/sweep'][
            'sweep_map']
        map = json.loads(map_text)
        # # generate all variations

        logger.debug("map=%s" % pformat(map))
        runs = _expand_variations(maps=[map], values={})
        logger.debug("runs=%s" % runs)


        rands = []
        if 'http://rmit.edu.au/schemas/input/hrmc' in run_settings:

            self.rand_index = run_settings['http://rmit.edu.au/schemas/input/hrmc']['iseed']
            logger.debug("rand_index=%s" % self.rand_index)
            # prep random seeds for each run based off original iseed
            # FIXME: inefficient for large random file
            # TODO, FIXME: this is potentially problematic if different
            # runs end up overlapping in the random numbers they utilise.
            # solution is to have separate random files per run or partition
            # big file up.
            try:
                rands = hrmcstages.generate_rands(settings=local_settings,
                start_range=0,
                end_range=-1,
                num_required=len(runs),
                start_index=self.rand_index)
                logger.debug("rands=%s" % rands)
            except Exception, e:
                logger.debug(e)
                raise

        # For each of the generated runs, copy across and modify input directory
        # and then schedule subrun of hrmc connector
        logger.debug("run_settings=%s" % run_settings)
        for i, context in enumerate(runs):
            # Duplicate input directory into runX duplicates
            logger.debug("run=%s" % context)
            run_counter = int(context['run_counter'])
            logger.debug("run_counter=%s" % run_counter)
            logger.debug("systemsetttings=%s" % pformat(run_settings['http://rmit.edu.au/schemas/input/system']))
            input_location = run_settings[
                'http://rmit.edu.au/schemas/input/system'][u'input_location']
            #input_url = smartconnector.get_url_with_pkey(local_settings,
            #    input_location, is_relative_path=False)
            #'file://127.0.0.1/myfiles/input'
            input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                    input_storage_settings['type'])
            input_url = smartconnector.get_url_with_pkey(input_storage_settings,
                input_prefix + os.path.join(input_storage_settings['ip_address'], input_storage_offset),
            is_relative_path=False)
            logger.debug("input_url=%s" % input_url)
            # job_dir contains some overriding context that this run is situated under
            # run_inputdir = os.path.join(self.job_dir,
            #     "run%s" % str(run_counter),
            #     "input_0", "initial")
            run_inputdir = os.path.join(self.job_dir,
                "run%s" % str(run_counter),
                "input_0",)
            logger.debug("run_inputdir=%s" % run_inputdir)
            run_iter_url = smartconnector.get_url_with_pkey(local_settings,
                run_inputdir, is_relative_path=False)
            logger.debug("run_iter_url=%s" % run_iter_url)
            storage.copy_directories(input_url, run_iter_url)

            # Q: copy payload_location to gridYY/payload_Z ? this would allow templating of this too????
            # TODO: can we have multiple values files per input_dir or just one.
            # if mulitple, then need template_name(s).  Otherwise, run stage templates
            # all need to refer to same value file...
            template_name = run_settings['http://rmit.edu.au/schemas/stages/sweep'][u'template_name']
            logger.debug("template_name=%s" % template_name)

            # Need to load up existing values, because original input_dir could
            # have contained values for the whole run

            values_map = {}
            try:
                values_url = smartconnector.get_url_with_pkey(
                    local_settings,
                    os.path.join(run_inputdir, "initial",
                        '%s_values' % template_name),
                    is_relative_path=False)

                logger.debug("values_url=%s" % values_url)
                values_content = hrmcstages.get_file(values_url)
                logger.debug("values_content=%s" % values_content)
                values_map = dict(json.loads(values_content))
            except IOError:
                logger.warn("no values file found")

            # include run variations into the values_map
            values_map.update(context)
            logger.debug("new values_map=%s" % values_map)
            hrmcstages.put_file(values_url, json.dumps(values_map))

            # new format for values map one per directory
            try:
                new_values_url = smartconnector.get_url_with_pkey(
                    local_settings,
                    os.path.join(run_inputdir, "initial",
                        'values'),
                    is_relative_path=False)
                logger.debug("new_values_url=%s" % new_values_url)
            except IOError:
                logger.warn("no values file found")

            hrmcstages.put_file(new_values_url, json.dumps(values_map))

            data = {}
            logger.debug("rs=%s" % pformat(run_settings))
            # for param_name, params in run_settings.items():
            #     logger.debug("param_name=%s params=%s" % (param_name, params))
            #     if str(param_name).startswith(self.hrmc_schema[:-1]):
            #         for key, value in params.items():
            #             logger.debug("key=%s value=%s" % (key, value))
            #             data['%s/%s' % (param_name, key)] = value
            #     else:
            #         logger.debug("no match to %s" % self.hrmc_schema)

            # data = dict([('%s/%s' % (param_name, key), value)
            #     for param_name, params in run_settings.items()
            #         for key, value in params.items()
            #             if str(param_name).startswith(subdirective_ns)])
            data = run_settings
            logger.debug("data=%s" % pformat(data))

            if len(rands):
                data["http://rmit.edu.au/schemas/input/hrmc"][u'iseed'] = rands[i]
            data["http://rmit.edu.au/schemas/input/system"]['input_location'] = "%s/run%s/input_0" % (self.job_dir, run_counter)
            #data['smart_connector'] = subdirective
            #data["http://rmit.edu.au/schemas/input/system"]['output_location'] = os.path.join(self.job_dir, subdirective)
            logger.debug("data=%s" % pformat(data))

            # data2 = {'smart_connector': 'hrmc',
            #             self.hrmc_schema + 'number_vm_instances': local_settings['number_vm_instances'],
            #             self.hrmc_schema + 'minimum_number_vm_instances': local_settings['minimum_number_vm_instances'],
            #             self.hrmc_schema + u'iseed': rands[i],
            #             self.hrmc_schema + 'max_seed_int': 1000,
            #             self.hrmc_schema + 'input_location':  "%s/run%s/input_0" % (self.job_dir, run_counter),
            #             self.hrmc_schema + 'optimisation_scheme': local_settings['optimisation_scheme'],
            #             self.hrmc_schema + 'threshold': str(local_settings['threshold']),
            #             self.hrmc_schema + 'fanout_per_kept_result': local_settings['fanout_per_kept_result'],
            #             self.hrmc_schema + 'error_threshold': str(local_settings['error_threshold']),
            #             self.hrmc_schema + 'max_iteration': local_settings['max_iteration'],
            #             self.hrmc_schema + 'pottype': local_settings['pottype'],
            #             self.hrmc_schema + 'experiment_id': local_settings['experiment_id'],
            #             self.system_schema + 'output_location': os.path.join(self.job_dir, 'hrmcrun')}

            # logger.debug("data2=%s" % pformat(data2))

            current_context = models.Context.objects.get(id=contextid)
            submit_subtask("nectar", subdirective, data, user, current_context)

            # api_host = "http://127.0.0.1"
            # url = "%s/api/v1/context/?format=json" % api_host

            # # this assumes all interim results kept in local storage
            # new_input_location = "%s/run%s/input_0" % (self.job_dir, run_counter)

            # # pass the sessionid cookie through to the internal API
            # cookies = dict(self.request.COOKIES)
            # logger.debug("cookies=%s" % cookies)
            # headers = {'content-type': 'application/json'}
            # data = json.dumps({'smart_connector': 'smartconnector_hrmc',
            #             self.hrmc_schema+'number_vm_instances': local_settings['number_vm_instances'],
            #             self.hrmc_schema+'minimum_number_vm_instances': local_settings['minimum_number_vm_instances'],
            #             self.hrmc_schema+u'iseed': rands[i],
            #             self.hrmc_schema+'max_seed_int': 1000,
            #             self.hrmc_schema+'input_location':  new_input_location,
            #             self.hrmc_schema+'optimisation_scheme': local_settings['optimisation_scheme'],
            #             self.hrmc_schema+'threshold': str(local_settings['threshold']),
            #             self.hrmc_schema+'fanout_per_kept_result': local_settings['fanout_per_kept_result'],
            #             self.hrmc_schema+'error_threshold': str(local_settings['error_threshold']),
            #             self.hrmc_schema+'max_iteration': local_settings['max_iteration'],
            #             self.hrmc_schema+'pottype': local_settings['pottype'],
            #             self.hrmc_schema+'experiment_id': local_settings['experiment_id'],
            #             self.system_schema+'output_location': os.path.join(self.job_dir, 'hrmcrun') })

            # r = requests.post(url,
            #     data=data,
            #     headers=headers,
            #     cookies=cookies)

            # # TODO: need to check for status_code and handle failures.

            # logger.debug("r.json=%s" % r.json)
            # logger.debug("r.text=%s" % r.text)
            # logger.debug("r.headers=%s" % r.headers)
            # header_location = r.headers['location']
            # logger.debug("header_location=%s" % header_location)
            # new_context_uri = header_location[len(api_host):]
            # logger.debug("new_context_uri=%s" % new_context_uri)
        smartconnector.success(run_settings, "0: finished")


    def output(self, run_settings):
        logger.debug("sweep output")
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/sweep',
            {})[u'sweep_done'] = 1
        #run_settings[self.computation_platform_schema] = self.computation_platform
        '''
        for k, v in self.computation_platform.items():
            run_settings.setdefault(self.computation_platform_schema,
            {})[k] = v
            #run_settings[k] = k
        '''
        logger.debug('interesting run_settings=%s' % run_settings)
        return run_settings


def submit_subtask(platform, directive_name, data, user, parentcontext):
    # directive_args = []
    # for metadata in data:
    #     arg_metadata = {}
    #     for schema,v in metadata.items():
    #         ns, key = os.path.split(schema)
    #         if ns:
    #             d = arg_metadata.setdefault(ns, [])
    #             d.append((key, v))
    #     logger.debug("args=%s" % pformat(arg_metadata))
    #     arg_meta = [[schema] + arg_metadata[schema] for schema in arg_metadata]
    #     arg_meta.insert(0, "")
    #     directive_args.append(arg_meta)
    directive_args = []
    for schema in data.keys():
        keys = data[schema]
        d = []
        logger.debug("keys=%s" % keys)
        for k, v in keys.items():
            d.append((k, v))
        d.insert(0, schema)
        directive_args.append(d)

    directive_args.insert(0, '')
    directive_args = [directive_args]
    logger.debug("directive_args=%s" % pformat(directive_args))
    logger.debug('directive_name=%s' % directive_name)
    try:
        (task_run_settings, command_args, run_context) \
            = hrmcstages.make_runcontext_for_directive(
                platform,
                directive_name, directive_args, {}, user, parent=parentcontext)
    except InvalidInputError, e:
        logger.error(str(e))
    logger.debug("sweep process done")
        #     system_dict = {
        #     u'system': u'settings',
        #     u'output_location': os.path.join(self.job_dir, 'hrmcrun')}

        #     system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        #     platform = "nectar"
        #     directive_name = "smartconnector_hrmc"
        #     directive_args = []

        #     run_inputdir = os.path.join(self.job_dir,
        #         "run%s" % str(run_counter),
        #         "input_0", "initial")

        #     # this assumes all interim results kept in local storage
        #     new_input_location = "%s/run%s/input_0" % (self.job_dir, run_counter)

        #     directive_args.append(
        #         ['',
        #             ['http://rmit.edu.au/schemas/hrmc',
        #                 ('number_vm_instances', local_settings['number_vm_instances']),
        #                 ('minimum_number_vm_instances', local_settings['minimum_number_vm_instances']),
        #                 (u'iseed', rands[i]),
        #                 ('max_seed_int', 1000),
        #                 ('input_location',  new_input_location),
        #                 ('optimisation_scheme', local_settings['optimisation_scheme']),
        #                 ('threshold', local_settings['threshold']),
        #                 ('error_threshold', local_settings['error_threshold']),
        #                 ('fanout_per_kept_result', local_settings['fanout_per_kept_result']),
        #                 ('max_iteration', local_settings['max_iteration']),
        #                 # We assume that each subtask puts results into same mytardis experiment
        #                 ('experiment_id', local_settings['experiment_id']),
        #                 ('pottype', local_settings['pottype'])
        #             ]
        #         ])

        #     logger.debug("directive_name=%s" % directive_name)
        #     logger.debug("directive_args=%s" % directive_args)
        #     try:
        #         (task_run_settings, command_args, run_context) \
        #             = hrmcstages.make_runcontext_for_directive(
        #             platform,
        #             directive_name,
        #             directive_args, system_settings, user)

        #     except InvalidInputError, e:
        #         logger.error(str(e))
        # logger.debug("sweep process done")


def _expand_variations(maps, values):
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
        logger.debug("map_ranges=%s" % map_ranges)
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

