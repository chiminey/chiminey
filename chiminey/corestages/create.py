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

from chiminey.corestages.stage import Stage
from chiminey.runsettings import (
    getval, setval, SettingNotFoundException)
from chiminey import messages
from django.conf import settings as django_settings
from chiminey.smartconnectorscheduler import jobs
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)

from django.conf import settings as django_settings


class Create(Stage):
    def __init__(self, user_settings=None):
        #        self.group_id = ''
        self.platform_type = None
        logger.debug("Create stage initialized")

    def is_triggered(self, run_settings):
        """
            Return True if configure done and no nodes are created
        """
        try:
            configure_done = int(getval(run_settings,
                '%s/stages/configure/configure_done' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            return False
        try:
            create_done = int(getval(run_settings,
                '%s/stages/create/create_done' % django_settings.SCHEMA_PREFIX))
            if create_done:
               return False
        except (SettingNotFoundException, ValueError):
            pass
        try:
            self.created_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX))
        except (SettingNotFoundException, ValueError):
            self.created_nodes = []
            return True
        return False

    def process(self, run_settings):
        #messages.info(run_settings, "1: create")
        comp_pltf_settings = self.get_platform_settings(
            run_settings, '%s/platform/computation' % django_settings.SCHEMA_PREFIX)
        logger.debug("comp_pltf_settings=%s" % comp_pltf_settings)
        try:
            platform_type = comp_pltf_settings['platform_type']
        except KeyError, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        logger.debug("platform_type=%s" % platform_type)

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
            self.strategy.set_create_settings(run_settings, local_settings)
            local_settings.update(comp_pltf_settings)
            logger.debug('local_settings=%s' % local_settings)
        except SettingNotFoundException, e:
            logger.error(e)
            messages.error(run_settings, e)
            return

        self.group_id, self.created_nodes = self.strategy.create_resource(local_settings)

    def output(self, run_settings):
        """
        Inserting a new group if into run settings.
        """
        logger.debug('output')
        setval(run_settings,
                       "%s/stages/create/created_nodes" % django_settings.SCHEMA_PREFIX,
                       self.created_nodes)
        setval(run_settings,
                       "%s/stages/create/create_done" % django_settings.SCHEMA_PREFIX,
                       1)
        logger.debug("Updated run settings %s" % run_settings)
        return run_settings
