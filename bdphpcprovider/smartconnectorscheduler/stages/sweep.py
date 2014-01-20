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
import json
from itertools import product
from pprint import pformat

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import models, platform, storage
from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler.mytardis import (
    create_graph_paramset,
    create_paramset)

logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Sweep(Stage):

    def __init__(self, user_settings=None):
        self.numbfile = 0
        logger.debug("Sweep stage initialized")

    def triggered(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)
        if self._exists(run_settings,
            RMIT_SCHEMA + '/stages/sweep',
            'sweep_done'):
            configure_done = int(run_settings[
                RMIT_SCHEMA + '/stages/sweep'][u'sweep_done'])
            return not configure_done
        return True

    def process(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)

        # Need to make copy because we pass on run_settings to sub connector
        # so any changes we make here to run_settings WILL be inherited
        from copy import deepcopy
        local_settings = deepcopy(run_settings[models.UserProfile.PROFILE_SCHEMA_NS])

        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/input/mytardis/experiment_id')
        smartconnector.copy_settings(local_settings, run_settings,
            RMIT_SCHEMA + '/system/random_numbers')
        local_settings['bdp_username'] = run_settings[
            RMIT_SCHEMA + '/bdp_userprofile']['username']

        logger.debug('local_settings=%s' % local_settings)

        contextid = int(run_settings[RMIT_SCHEMA + '/system'][
            u'contextid'])
        logger.debug("contextid=%s" % contextid)

        # if self._exists(run_settings,
        #     RMIT_SCHEMA + '/system',
        #     'parent_contextid'):
        #     parent_contextid = int(run_settings[RMIT_SCHEMA + '/system'][u'parent_contextid'])
        # else:
        #     parent_contextid = 0

        computation_platform_name = run_settings[
            RMIT_SCHEMA + '/input/system/compplatform']['computation_platform']
        run_settings[RMIT_SCHEMA + '/platform/computation'] = {}
        run_settings[RMIT_SCHEMA + '/platform/computation'][
            'platform_url'] = computation_platform_name

        output_location = run_settings[RMIT_SCHEMA + '/input/system'][u'output_location']
        output_location_list = output_location.split('/')
        output_storage_name = output_location_list[0]
        output_storage_offset = ''
        if len(output_location_list) > 1:
            output_storage_offset = os.path.join(*output_location_list[1:])
        logger.debug('output_storage_offset=%s' % output_storage_offset)

        run_settings[RMIT_SCHEMA + '/platform/storage/output'] = {}
        run_settings[RMIT_SCHEMA + '/platform/storage/output'][
            'platform_url'] = output_storage_name
        run_settings[RMIT_SCHEMA + '/platform/storage/output']['offset'] = \
            os.path.join(output_storage_offset, 'sweep%s' % contextid)

        minput_location = run_settings[RMIT_SCHEMA + '/input/system'][
            u'input_location']
        input_location_list = minput_location.split('/')
        input_storage_name = input_location_list[0]
        input_storage_offset = ''
        if len(input_location_list) > 1:
            input_storage_offset = os.path.join(*input_location_list[1:])
        logger.debug('input_storage_offset=%s' % input_storage_offset)
        run_settings[RMIT_SCHEMA + '/platform/storage/input'] = {}
        run_settings[RMIT_SCHEMA + '/platform/storage/input'][
            'platform_url'] = input_storage_name
        bdp_username = run_settings[RMIT_SCHEMA + '/bdp_userprofile'][
            'username']
        logger.debug("bdp_username=%s" % bdp_username)
        input_storage_url = run_settings[
            RMIT_SCHEMA + '/platform/storage/input']['platform_url']
        input_storage_settings = platform.get_platform_settings(
            input_storage_url,
            bdp_username)
        run_settings[RMIT_SCHEMA + '/platform/storage/input'][
            'offset'] = input_storage_offset

        try:
            self.experiment_id = int(smartconnector.get_existing_key(
                run_settings,
                RMIT_SCHEMA + '/input/mytardis/experiment_id'))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0

        subdirective = run_settings[RMIT_SCHEMA + '/stages/sweep']['directive']
        current_context = models.Context.objects.get(id=contextid)
        user = current_context.owner.user.username
        # TODO: replace with scratch space computation platform space
        self.scratch_platform = '%ssweep%s' % (
            platform.get_scratch_platform(),
            contextid)

        # TODO: this is domain-specific so should be a parameter of the
        # stage.
        if subdirective == "vasp":
            self.experiment_id = self._make_mytardis_exp(
                run_settings=run_settings,
                experiment_id=self.experiment_id,
                experiment_paramset=[
                    create_paramset("remotemake", []),
                    create_graph_paramset("expgraph",
                        name="makeexp1",
                        graph_info={"axes":["num_kp", "energy"],
                            "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp",
                            "makedset/toten"]]),
                    create_graph_paramset("expgraph",
                        name="makeexp2",
                        graph_info={"axes":["encut", "energy"],
                            "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/encut",
                            "makedset/toten"]]),
                    create_graph_paramset("expgraph",
                        name="makeexp3",
                        graph_info={"axes":["num_kp", "encut", "TOTEN"],
                            "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp", "makedset/encut",
                            "makedset/toten"]]),
                    ],
                output_location=self.scratch_platform)

            run_settings[RMIT_SCHEMA + '/input/mytardis'][
                'experiment_id'] = self.experiment_id
        elif subdirective == "remotemake":
            self.experiment_id = self._make_mytardis_exp(
                run_settings=run_settings,
                experiment_id=self.experiment_id,
                experiment_paramset=[
                    create_paramset("remotemake", [])],
                output_location=self.scratch_platform)
        elif subdirective == "hrmc":
            pass

        if '%s/input/mytardis' % RMIT_SCHEMA in run_settings:
                run_settings[RMIT_SCHEMA + '/input/mytardis'][
            'experiment_id'] = str(self.experiment_id)

        # # generate all variations
        map_text = run_settings[RMIT_SCHEMA + '/input/sweep']['sweep_map']
        sweep_map = json.loads(map_text)
        logger.debug("sweep_map=%s" % pformat(sweep_map))
        runs = _expand_variations(maps=[sweep_map], values={})
        logger.debug("runs=%s" % runs)

        # Create random numbers if needed
        rands = []
        if RMIT_SCHEMA + '/input/hrmc' in run_settings:

            # TODO: move iseed out of hrmc into separate generic schema
            # to use on any sweepable connector and make this function
            # completely hrmc independent.

            self.rand_index = run_settings[
                RMIT_SCHEMA + '/input/hrmc']['iseed']
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
                logger.error(e)
                raise

        # load initial values map in the input directory which
        # contains variable to use for all subdirectives
        starting_map = {}
        try:
            input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                    input_storage_settings['type'])
            values_url = smartconnector.get_url_with_pkey(
                input_storage_settings,
                input_prefix + os.path.join(input_storage_settings['ip_address'],
                input_storage_offset, "initial", "values"),
            is_relative_path=False)
            logger.debug("values_url=%s" % values_url)
            values_e_url = smartconnector.get_url_with_pkey(
                local_settings,
                values_url,
                is_relative_path=False)
            logger.debug("values_url=%s" % values_e_url)
            values_content = hrmcstages.get_file(values_e_url)
            logger.debug("values_content=%s" % values_content)
            starting_map = dict(json.loads(values_content))
        except IOError:
            logger.warn("no starting values file found")
        logger.debug("starting_map after initial values=%s"
            % pformat(starting_map))

        # Copy form input values info starting map
        # FIXME: could have name collisions between form inputs and
        # starting values.
        for ns in run_settings:
            if ns.startswith(RMIT_SCHEMA + "/input"):
                for k, v in run_settings[ns].items():
                    starting_map[k] = v
        logger.debug("starting_map after form=%s" % pformat(starting_map))

        # Get input_url directory
        input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                input_storage_settings['type'])
        input_url = smartconnector.get_url_with_pkey(input_storage_settings,
            input_prefix + os.path.join(input_storage_settings['ip_address'],
                input_storage_offset),
        is_relative_path=False)
        logger.debug("input_url=%s" % input_url)

        # For each of the generated runs, copy accross initial input
        # to individual input directories with varaition values,
        # and then schedule subrun of sub directive
        logger.debug("run_settings=%s" % run_settings)
        for i, context in enumerate(runs):
            # Duplicate input directory into runX duplicates
            logger.debug("context=%s" % context)

            run_counter = int(context['run_counter'])
            logger.debug("run_counter=%s" % run_counter)
            logger.debug("systemsetttings=%s" % pformat(run_settings[
                RMIT_SCHEMA + '/input/system']))
            run_inputdir = os.path.join(self.scratch_platform,
                "run%s" % str(run_counter),
                "input_0",)
            logger.debug("run_inputdir=%s" % run_inputdir)
            run_iter_url = smartconnector.get_url_with_pkey(local_settings,
                run_inputdir, is_relative_path=False)
            logger.debug("run_iter_url=%s" % run_iter_url)

            storage.copy_directories(input_url, run_iter_url)

            # TODO: can we have multiple values files per input_dir or just one.
            # if mulitple, then need template_name(s).  Otherwise, run stage templates
            # all need to refer to same value file...

            # Need to load up existing values, because original input_dir could
            # have contained values for the whole run
            if self._exists(run_settings,
                RMIT_SCHEMA + '/stages/sweep',
                'template_name'):

                # TODO: This code is deprecated, as should rely purely on "values"
                # file and any *_template files, rather than a single
                # template_name
                template_name = run_settings[RMIT_SCHEMA + '/stages/sweep'][
                    u'template_name']
                logger.debug("template_name=%s" % template_name)
                v_map = {}
                try:
                    values_url = smartconnector.get_url_with_pkey(
                        local_settings,
                        os.path.join(run_inputdir, "initial",
                            '%s_values' % template_name),
                        is_relative_path=False)
                    logger.debug("values_url=%s" % values_url)
                    values_content = hrmcstages.get_file(values_url)
                    logger.debug("values_content=%s" % values_content)
                    v_map = dict(json.loads(values_content), indent=4)
                except IOError:
                    logger.warn("no values file found")
                v_map.update(starting_map)
                v_map.update(context)
                logger.debug("new v_map=%s" % v_map)
                hrmcstages.put_file(values_url, json.dumps(v_map, indent=4))

            v_map = {}
            try:
                values_url = smartconnector.get_url_with_pkey(
                    local_settings,
                    os.path.join(run_inputdir, "initial",
                        'values'),
                    is_relative_path=False)
                logger.debug("values_url=%s" % values_url)
                values_content = hrmcstages.get_file(values_url)
                logger.debug("values_content=%s" % values_content)
                v_map = dict(json.loads(values_content), )
            except IOError:
                logger.warn("no values file found")
            v_map.update(starting_map)
            v_map.update(context)
            logger.debug("new v_map=%s" % v_map)
            hrmcstages.put_file(values_url, json.dumps(v_map, indent=4))

            # Prepare subdirective run_settings
            logger.debug("run_settings=%s" % pformat(run_settings))
            if len(rands):
                run_settings[RMIT_SCHEMA + '/input/hrmc'][u'iseed'] = rands[i]
            run_settings[RMIT_SCHEMA + "/input/system"]['input_location'] =  \
                "%s/run%s/input_0" % (self.scratch_platform, run_counter)
            run_settings[RMIT_SCHEMA + "/input/system"]['input_location'] =  \
                "%s/run%s/input_0" % (self.scratch_platform, run_counter)

            minput_location = "local/sweep%s/run%s/input_0" % (contextid, run_counter)
            input_location_list = minput_location.split('/')
            input_storage_name = input_location_list[0]
            input_storage_offset = ''
            if len(input_location_list) > 1:
                input_storage_offset = os.path.join(*input_location_list[1:])
            logger.debug('input_storage_offset=%s' % input_storage_offset)
            run_settings[RMIT_SCHEMA + '/platform/storage/input'] = {}
            run_settings[RMIT_SCHEMA + '/platform/storage/input'][
                'platform_url'] = input_storage_name
            bdp_username = run_settings[RMIT_SCHEMA + '/bdp_userprofile'][
                'username']
            input_storage_url = run_settings[
                RMIT_SCHEMA + '/platform/storage/input']['platform_url']
            input_storage_settings = platform.get_platform_settings(
                input_storage_url,
                bdp_username)
            run_settings[RMIT_SCHEMA + '/platform/storage/input'][
                'offset'] = input_storage_offset

            logger.debug("run_settings=%s" % pformat(run_settings))

            _submit_subtask("nectar", subdirective, run_settings, user, current_context)
        smartconnector.success(run_settings, "0: creating sub jobs")

    def output(self, run_settings):
        logger.debug("sweep output")
        run_settings.setdefault(
            RMIT_SCHEMA + '/stages/sweep',
            {})[u'sweep_done'] = 1
        logger.debug('interesting run_settings=%s' % run_settings)

        if '%s/input/mytardis' % RMIT_SCHEMA in run_settings:
                run_settings[RMIT_SCHEMA + '/input/mytardis'][
            'experiment_id'] = str(self.experiment_id)

        return run_settings

    def _make_mytardis_exp(
            self, run_settings,
            experiment_id, experiment_paramset,
            output_location):
        bdp_username = run_settings[
            RMIT_SCHEMA + '/bdp_userprofile']['username']
        mytardis_url = run_settings[
            RMIT_SCHEMA + '/input/mytardis']['mytardis_platform']
        mytardis_settings = platform.get_platform_settings(
            mytardis_url,
            bdp_username)
        logger.debug(mytardis_settings)
        if mytardis_settings['mytardis_host']:
            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-1:]))
            ename = _get_exp_name_for_input(output_location)
            logger.debug("ename=%s" % ename)
            experiment_id = mytardis.create_experiment(
                settings=mytardis_settings,
                exp_id=self.experiment_id,
                experiment_paramset=experiment_paramset,
                expname=ename)
        return experiment_id


def _submit_subtask(platform, directive_name, data, user, parentcontext):
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


def _expand_variations(maps, values):
    """
    Based on maps, generate all range variations from the template
    """
    # FIXME: doesn't handle multiple template files together
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
            context['run_counter'] = numbfile
            numbfile += 1
            res.append(context)
    return res
