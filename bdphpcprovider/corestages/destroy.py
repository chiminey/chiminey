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
from bdphpcprovider.corestages import stage, strategies
from bdphpcprovider import messages

from bdphpcprovider.runsettings import getval, setvals, SettingNotFoundException

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Destroy(stage.Stage):

    def __init__(self, user_settings=None):
        logger.debug('Destroy stage initialised')

    def is_triggered(self, run_settings):
        try:
            converged = int(getval(run_settings, '%s/stages/converge/converged' % RMIT_SCHEMA))
            logger.debug("converged=%s" % converged)
        except (ValueError, SettingNotFoundException) as e:
            return False
        if converged:
            try:
                run_finished = int(getval(run_settings,
                                   '%s/stages/destroy/run_finished'
                                        % RMIT_SCHEMA))
            except (ValueError, SettingNotFoundException) as e:
                return True
            return not run_finished
        return False

    def process(self, run_settings):
        try:
            self.id = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.id = 0
        try:
            self.created_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/create/created_nodes' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.created_nodes = []

        try:
            self.scheduled_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.scheduled_nodes = []

        try:
            self.bootstrapped_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            self.bootstrapped_nodes = []


        messages.info(run_settings, "%d: destroy" % self.id)
        comp_pltf_settings = self.get_platform_settings(
            run_settings, 'http://rmit.edu.au/schemas/platform/computation')
        try:
            platform_type = comp_pltf_settings['platform_type']
        except KeyError, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        if platform_type == 'nectar' or platform_type == 'csrack':
            self.strategy = strategies.CloudStrategy()
        elif platform_type == 'nci':
            self.strategy = strategies.ClusterStrategy()
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
            '%s/stages/destroy/run_finished' % RMIT_SCHEMA: 1
               })
        setvals(run_settings, {
            '%s/stages/create/created_nodes' % RMIT_SCHEMA: self.created_nodes
               })
        setvals(run_settings, {
            '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA: self.scheduled_nodes
               })
        setvals(run_settings, {
            '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA: self.bootstrapped_nodes
               })
        messages.success(run_settings, "%d: finished" % self.id)
        return run_settings
