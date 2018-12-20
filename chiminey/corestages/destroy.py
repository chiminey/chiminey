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
from chiminey.corestages import stage, strategies
from chiminey import messages

from chiminey.runsettings import getval, setvals, SettingNotFoundException


from django.conf import settings as django_settings
from chiminey.smartconnectorscheduler import jobs
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)

from django.conf import settings as django_settings


class Destroy(stage.Stage):

    def __init__(self, user_settings=None):
        logger.debug('Destroy stage initialised')

    def is_triggered(self, run_settings):
        try:
            converged = int(getval(run_settings, '%s/stages/converge/converged' % django_settings.SCHEMA_PREFIX))
            logger.debug("converged=%s" % converged)
        except (ValueError, SettingNotFoundException) as e:
            return False
        if converged:
            try:
                run_finished = int(getval(run_settings,
                                   '%s/stages/destroy/run_finished'
                                        % django_settings.SCHEMA_PREFIX))
            except (ValueError, SettingNotFoundException) as e:
                return True
            return not run_finished
        return False

    def process(self, run_settings):
        try:
            self.id = int(getval(run_settings, '%s/system/id' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.id = 0
        try:
            self.created_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.created_nodes = []

        try:
            self.scheduled_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.scheduled_nodes = []

        try:
            self.bootstrapped_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/bootstrap/bootstrapped_nodes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.bootstrapped_nodes = []


        #messages.info(run_settings, "%d: destroy" % self.id)
        comp_pltf_settings = self.get_platform_settings(
            run_settings, '%s/platform/computation' % django_settings.SCHEMA_PREFIX)
        try:
            platform_type = comp_pltf_settings['platform_type']
        except KeyError, e:
            logger.error(e)
            messages.error(run_settings, e)
            return

        # TODO: cache is as unlikely to change during execution
        for platform_hook in django_settings.PLATFORM_CLASSES:
            try:
                hook = jobs.safe_import(platform_hook, [], {})
            except ImproperlyConfigured as  e:
                logger.error("Cannot load platform hook %s" % e)
                continue
            logger.debug("hook=%s" % hook)
            logger.debug("hook.get_platform_types=%s" % hook.get_platform_types())
            logger.debug("platform_type=%s" % platform_type)
            if platform_type in hook.get_platform_types():
                self.strategy = hook.get_strategy(platform_type)
                logger.debug("self.strategy=%s" % self.strategy)
                break
        # if platform_type in ['nectar', 'csrack', 'amazon']:
        #     self.strategy = strategies.CloudStrategy()
        # elif platform_type in ['nci']:
        #     self.strategy = strategies.ClusterStrategy()
        local_settings = {}
        try:
            self.strategy.set_destroy_settings(run_settings, local_settings)
            local_settings.update(comp_pltf_settings)
            logger.debug('local_settings=%s' % local_settings)
        except SettingNotFoundException, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        logger.debug('started')
        self.strategy.destroy_resource(self, run_settings, local_settings)
        logger.debug('ended')

    def output(self, run_settings):
        setvals(run_settings, {
            '%s/stages/destroy/run_finished' % django_settings.SCHEMA_PREFIX: 1
               })
        setvals(run_settings, {
            '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX: self.created_nodes
               })
        setvals(run_settings, {
            '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX: self.scheduled_nodes
               })
        setvals(run_settings, {
            '%s/stages/bootstrap/bootstrapped_nodes' % django_settings.SCHEMA_PREFIX: self.bootstrapped_nodes
               })
        messages.success(run_settings, "%d: Completed" % self.id)
        return run_settings
