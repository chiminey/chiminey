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
import json
from itertools import product
from pprint import pformat

from chiminey.corestages.stage import Stage
from chiminey.smartconnectorscheduler import models
from chiminey.smartconnectorscheduler import jobs

from chiminey import messages
from chiminey.platform import manage
from chiminey import storage
from chiminey import mytardis

from chiminey.runsettings import getval, getvals, \
    setval, update, get_schema_namespaces, SettingNotFoundException
from chiminey.storage import get_url_with_credentials


logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"
FIRST_ITERATION_DIR = "input_0"
SUBDIRECTIVE_DIR = "run%(run_counter)s"

VALUES_MAP_TEMPLATE_FILE = '%(template_name)s_values'
VALUES_MAP_FILE = "values"


class Sweep(Stage):

    def __init__(self, user_settings=None):
        self.numbfile = 0
        logger.debug("Sweep stage initialized")

    def is_triggered(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)

        try:
            configure_done = int(getval(run_settings,
                '%s/stages/sweep/sweep_done' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            return True

        return not configure_done

    def _get_sweep_name(self, run_settings):
        try:
            sweep_name = getval(run_settings, '%s/directive_profile/sweep_name' % RMIT_SCHEMA)
        except SettingNotFoundException:
            sweep_name = 'unknown_sweep'
        return sweep_name

    def process(self, run_settings):
        logger.debug('run_settings=%s' % run_settings)

        # Need to make copy because we pass on run_settings to sub connector
        # so any changes we make here to run_settings WILL be inherited
        def make_local_settings(run_settings):
            from copy import deepcopy
            local_settings = deepcopy(getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS))

            update(local_settings, run_settings,
                    RMIT_SCHEMA + '/system/platform',
                    # RMIT_SCHEMA + '/input/mytardis/experiment_id',
                    # RMIT_SCHEMA + '/system/random_numbers',
                   )
            local_settings['bdp_username'] = getval(
                run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
            return local_settings

        local_settings = make_local_settings(run_settings)
        logger.debug('local_settings=%s' % local_settings)

        setval(run_settings,
               '%s/platform/computation/platform_url' % RMIT_SCHEMA,
               getval(run_settings,
                      '%s/input/system/compplatform/computation_platform'
                            % RMIT_SCHEMA))

        def _parse_output_location(run_settings, location):

            loc_list = location.split('/')
            name = loc_list[0]
            offset = ''
            if len(loc_list) > 1:
                offset = os.path.join(*loc_list[1:])
            logger.debug('offset=%s' % offset)
            return name, offset

        contextid = int(getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA))
        logger.debug("contextid=%s" % contextid)
        sweep_name = self._get_sweep_name(run_settings)
        logger.debug("sweep_name=%s" % sweep_name)

        output_loc = self.output_exists(run_settings)
        if output_loc:
            location = getval(run_settings, output_loc)
            output_storage_name, output_storage_offset = \
                _parse_output_location(run_settings, location)
            setval(run_settings,
                   '%s/platform/storage/output/platform_url' % RMIT_SCHEMA,
                   output_storage_name)
            setval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA,
                   os.path.join(output_storage_offset, '%s%s' % (sweep_name, contextid)))

        def _parse_input_location(run_settings, location):
            loc_list = location.split('/')
            name = loc_list[0]
            offset = ''
            if len(loc_list) > 1:
                offset = os.path.join(*loc_list[1:])
            logger.debug('offset=%s' % offset)
            return (name, offset)

        input_loc = self.input_exists(run_settings)
        if input_loc:
            location = getval(run_settings, input_loc)
            input_storage_name, input_storage_offset = \
                _parse_input_location(run_settings, location)
            setval(run_settings, '%s/platform/storage/input/platform_url' % RMIT_SCHEMA,
                   input_storage_name)
            # store offsets
            setval(run_settings,
                   '%s/platform/storage/input/offset' % RMIT_SCHEMA,
                   input_storage_offset)

        # TODO: replace with scratch space computation platform space
        self.scratch_platform = '%s%s%s' % (
            manage.get_scratch_platform(), sweep_name,
            contextid)

        # mytardis

        try:
            self.experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        except KeyError:
            self.experiment_id = 0
        except ValueError:
            self.experiment_id = 0
        try:
            curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
        except SettingNotFoundException:
            curate_data = False
        if curate_data:
            self.experiment_id = self.curate_data(run_settings, self.experiment_id)
        setval(run_settings,
               '%s/input/mytardis/experiment_id' % RMIT_SCHEMA,
               str(self.experiment_id))

        # generate all variations
        map_text = getval(run_settings, '%s/input/sweep/sweep_map' % RMIT_SCHEMA)
        # map_text = run_settings[RMIT_SCHEMA + '/input/sweep']['sweep_map']
        sweep_map = json.loads(map_text)
        logger.debug("sweep_map=%s" % pformat(sweep_map))
        runs = _expand_variations(maps=[sweep_map], values={})
        logger.debug("runs=%s" % runs)

        # Create random numbers if needed
        # TODO: move iseed out of hrmc into separate generic schema
        # to use on any sweepable connector and make this function
        # completely hrmc independent.

        rands = []

        try:
            self.rand_index = getval(run_settings, '%s/input/hrmc/iseed' % RMIT_SCHEMA)
            logger.debug("rand_index=%s" % self.rand_index)
        except SettingNotFoundException:
            pass
        else:
            # prep random seeds for each run based off original iseed
            # FIXME: inefficient for large random file
            # TODO, FIXME: this is potentially problematic if different
            # runs end up overlapping in the random numbers they utilise.
            # solution is to have separate random files per run or partition
            # big file up.

            try:
                num_url = getval(run_settings, "%s/system/random_numbers" % RMIT_SCHEMA)
            except SettingNotFoundException:
                pass
            else:
                try:
                    local_settings['random_numbers'] = num_url
                    rands = jobs.generate_rands(settings=local_settings,
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
        if input_loc:

            input_storage_settings = self.get_platform_settings(
                run_settings, 'http://rmit.edu.au/schemas/platform/storage/input')
            try:
                input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                        input_storage_settings['type'])

                values_url = get_url_with_credentials(
                    input_storage_settings,
                    input_prefix + os.path.join(input_storage_settings['ip_address'],
                        input_storage_offset, "initial", VALUES_MAP_FILE),
                    is_relative_path=False)
                logger.debug("values_url=%s" % values_url)

                values_e_url = get_url_with_credentials(
                    local_settings,
                    values_url,
                    is_relative_path=False)
                logger.debug("values_url=%s" % values_e_url)
                values_content = storage.get_file(values_e_url)
                logger.debug("values_content=%s" % values_content)
                starting_map = dict(json.loads(values_content))
            except IOError:
                logger.warn("no starting values file found")
            except ValueError:
                logger.error("problem parsing contents of %s" % VALUES_MAP_FILE)
                pass
            logger.debug("starting_map after initial values=%s"
                % pformat(starting_map))

        # Copy form input values info starting map
        # FIXME: could have name collisions between form inputs and
        # starting values.
        for ns in run_settings:
            if ns.startswith(RMIT_SCHEMA + "/input"):
                # for k, v in run_settings[ns].items():
                for k, v in getvals(run_settings, ns).items():
                    starting_map[k] = v
        logger.debug("starting_map after form=%s" % pformat(starting_map))

        # FIXME: we assume we will always have input directory

        # Get input_url directory
        input_url = ""
        if input_loc:
            input_prefix = '%s://%s@' % (input_storage_settings['scheme'],
                                    input_storage_settings['type'])
            input_url = get_url_with_credentials(input_storage_settings,
                input_prefix + os.path.join(input_storage_settings['ip_address'],
                    input_storage_offset),
            is_relative_path=False)
            logger.debug("input_url=%s" % input_url)

        current_context = models.Context.objects.get(id=contextid)
        user = current_context.owner.user.username

        # For each of the generated runs, copy across initial input
        # to individual input directories with variation values,
        # and then schedule subrun of sub directive
        logger.debug("run_settings=%s" % run_settings)
        for i, context in enumerate(runs):

            run_counter = int(context['run_counter'])
            logger.debug("run_counter=%s" % run_counter)
            run_inputdir = os.path.join(self.scratch_platform,
                SUBDIRECTIVE_DIR % {'run_counter': str(run_counter)},
                FIRST_ITERATION_DIR,)
            logger.debug("run_inputdir=%s" % run_inputdir)
            run_iter_url = get_url_with_credentials(local_settings,
                run_inputdir, is_relative_path=False)
            logger.debug("run_iter_url=%s" % run_iter_url)

            # Duplicate any input_directory into runX duplicates
            if input_loc:
                logger.debug("context=%s" % context)
                logger.debug("systemsettings=%s"
                         % pformat(getvals(run_settings, RMIT_SCHEMA + '/input/system')))
                storage.copy_directories(input_url, run_iter_url)

            # Need to load up existing values, because original input_dir could
            # have contained values for the whole run
            # This code is deprecated in favour of single values file.
            self.error_detected = False


            try:
                template_name = getval(run_settings,
                                       '%s/stages/sweep/template_name'
                                            % RMIT_SCHEMA)
            except SettingNotFoundException:
                pass
            else:
                logger.debug("template_name=%s" % template_name)
                v_map = {}
                try:
                    values_url = get_url_with_credentials(
                        local_settings,
                        os.path.join(run_inputdir, "initial",
                             VALUES_MAP_TEMPLATE_FILE % {'template_name': template_name}),
                        is_relative_path=False)
                    logger.debug("values_url=%s" % values_url)
                    values_content = storage.get_file(values_url)
                    logger.debug("values_content=%s" % values_content)
                    v_map = dict(json.loads(values_content), indent=4)
                except IOError:
                    logger.warn("no values file found")
                except ValueError:
                    logger.error("problem parsing contents of %s" % VALUES_MAP_FILE)
                    pass
                v_map.update(starting_map)
                v_map.update(context)
                logger.debug("new v_map=%s" % v_map)
                storage.put_file(values_url, json.dumps(v_map, indent=4))

            v_map = {}
            try:
                values_url = get_url_with_credentials(
                    local_settings,
                    os.path.join(run_inputdir, "initial",
                        VALUES_MAP_FILE),
                    is_relative_path=False)
                logger.debug("values_url=%s" % values_url)
                values_content = storage.get_file(values_url)
                logger.debug("values_content=%s" % values_content)
                v_map = dict(json.loads(values_content), )
            except IOError:
                logger.warn("no values file found")
            except ValueError:
                logger.error("problem parsing contents of %s" % VALUES_MAP_FILE)
                pass
            v_map.update(starting_map)
            v_map.update(context)
            logger.debug("new v_map=%s" % v_map)
            storage.put_file(values_url, json.dumps(v_map, indent=4))

            # Set random numbers for subdirective
            logger.debug("run_settings=%s" % pformat(run_settings))
            if rands:
                setval(run_settings, '%s/input/hrmc/iseed' % RMIT_SCHEMA, rands[i])

            if input_loc:
                # Set revised input_location for subdirective
                setval(run_settings, input_loc,
                    "%s/%s/%s" % (self.scratch_platform,
                                    SUBDIRECTIVE_DIR
                                        % {'run_counter': str(run_counter)},
                                    FIRST_ITERATION_DIR))

            # Redirect input
            run_input_storage_name, run_input_storage_offset = \
                _parse_input_location(run_settings,
                    "local/sweep%s/run%s/input_0" % (contextid, run_counter))
            # setval(run_settings,
            #        '%s/platform/storage/input/platform_url' % RMIT_SCHEMA,
            #        run_input_storage_name)
            # setval(run_settings,
            #        '%s/platform/storage/input/offset' % RMIT_SCHEMA,
            #        run_input_storage_offset)

            logger.debug("run_settings=%s" % pformat(run_settings))
            try:
                _submit_subdirective("nectar", run_settings, user, current_context)
            except Exception, e:
                logger.error(e)
                raise e

    def output(self, run_settings):
        logger.debug("sweep output")

        setval(run_settings, '%s/stages/sweep/sweep_done' % RMIT_SCHEMA, 1)
        logger.debug('interesting run_settings=%s' % run_settings)

        try:
            if getvals(run_settings, '%s/input/mytardis' % RMIT_SCHEMA):
                setval(run_settings,
                       '%s/input/mytardis/experiment_id' % RMIT_SCHEMA,
                       str(self.experiment_id))
        except SettingNotFoundException:
            pass

        if not self.error_detected:
            messages.success(run_settings, "0: completed")
        return run_settings

    def curate_data(self, run_settings, experiment_id):
        # TODO: this is a domain-specific so this function should be overridden
        # in domain specfic mytardis class
        #TODO: By default, this class should NOT CREATE an experiment

        # try:
        #     experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
        # except SettingNotFoundException:
        #     experiment_id = 0
        # except ValueError:
        #     experiment_id = 0

        # experiment_id = post_mytardis_exp(
        #     run_settings=run_settings,
        #     experiment_id=experiment_id,
        #     output_location=self.scratch_platform)

        # return experiment_id

        return experiment_id


def _submit_subdirective(platform, run_settings, user, parentcontext):
    try:
        subdirective_name = getval(run_settings, '%s/stages/sweep/directive' % RMIT_SCHEMA)
    except SettingNotFoundException:
        logger.warn("cannot find subdirective_name name")
        raise

    directive_args = []
    for schema in get_schema_namespaces(run_settings):
        keys = getvals(run_settings, schema)
        d = []
        logger.debug("keys=%s" % keys)
        for k, v in keys.items():
            d.append((k, v))
        d.insert(0, schema)
        directive_args.append(d)
    directive_args.insert(0, '')
    directive_args = [directive_args]
    logger.debug("directive_args=%s" % pformat(directive_args))
    logger.debug('subdirective_name=%s' % subdirective_name)

    (task_run_settings, command_args, run_context) \
        = jobs.make_runcontext_for_directive(
            platform,
            subdirective_name, directive_args, {}, user, parent=parentcontext)

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


class HRMCSweep(Sweep):
    pass
    # def curate_data(self, run_settings):

    #     # mytardis
    #     try:
    #         subdirective = getval(run_settings, '%s/stages/sweep/directive' % RMIT_SCHEMA)
    #     except SettingNotFoundException:
    #         logger.warn("cannot find subdirective name")
    #         subdirective = ''
    #     try:
    #         experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id' % RMIT_SCHEMA))
    #     except SettingNotFoundException:
    #         experiment_id = 0
    #     except ValueError:
    #         experiment_id = 0

    #     if subdirective == "hrmc":
    #         experiment_id = post_mytardis_exp(
    #             run_settings=run_settings,
    #             experiment_id=experiment_id,
    #             output_location=self.scratch_platform)
    #     else:
    #         logger.warn("cannot find subdirective name")

    #     return experiment_id


def post_mytardis_exp(run_settings,
        experiment_id,
        output_location,
        experiment_paramset=[]):
    # TODO: move into mytardis package?
    bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)

    try:
        mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)
    except SettingNotFoundException:
        logger.error("mytardis_platform not set")
        return 0

    mytardis_settings = manage.get_platform_settings(
        mytardis_url,
        bdp_username)
    logger.debug(mytardis_settings)
    curate_data = getval(run_settings, '%s/input/mytardis/curate_data' % RMIT_SCHEMA)
    if curate_data:
        if mytardis_settings['mytardis_host']:
            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-1:]))
            ename = _get_exp_name_for_input(output_location)
            logger.debug("ename=%s" % ename)
            experiment_id = mytardis.create_experiment(
                settings=mytardis_settings,
                exp_id=experiment_id,
                experiment_paramset=experiment_paramset,
                expname=ename)
        else:
            logger.warn("no mytardis host specified")
    else:
        logger.warn('Data curation is off')
    return experiment_id
