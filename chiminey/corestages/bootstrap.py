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
from chiminey.smartconnectorscheduler.errors import PackageFailedError
from chiminey.runsettings import getval, setvals, SettingNotFoundException
from chiminey import messages
from chiminey.corestages import strategies


logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Bootstrap(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        logger.debug('Bootstrap stage initialised')

    def is_triggered(self, run_settings):
        try:
            self.created_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/create/created_nodes' % RMIT_SCHEMA))
            running_created_nodes = [x for x in self.created_nodes if str(x[3]) == 'running']
            logger.debug('running_created_nodes=%s' % running_created_nodes)
            if len(running_created_nodes) == 0:
                return False
        except (SettingNotFoundException, ValueError):
            return False
        try:
            self.bootstrapped_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA))
            logger.debug('bootstrapped nodes=%d, running created nodes = %d'
                         % (len(self.bootstrapped_nodes), len(running_created_nodes)))
            return len(self.bootstrapped_nodes) < len(running_created_nodes)
        except (SettingNotFoundException, ValueError):
            self.bootstrapped_nodes = []
            return True
        return False

    def process(self, run_settings):
        messages.info(run_settings, "0: bootstrapping nodes")
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
            self.strategy.set_bootstrap_settings(run_settings, local_settings)
            local_settings.update(comp_pltf_settings)
        except SettingNotFoundException, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        try:
            self.started = int(getval(
                run_settings, '%s/stages/bootstrap/started' % RMIT_SCHEMA))
        except SettingNotFoundException:
            self.started = 0
        except ValueError, e:
            logger.error(e)
        logger.debug('self.started=%d' % self.started)
        if not self.started:
            try:
                logger.debug('process to start')
                relative_path_suffix = self.get_relative_output_path(local_settings)
                self.strategy.start_multi_bootstrap_task(local_settings, relative_path_suffix)
            except PackageFailedError, e:
                logger.error("unable to start setup of packages: %s" % e)
            self.started = 1
        else:
            self.strategy.complete_bootstrap(self, local_settings)

    def output(self, run_settings):
        setvals(run_settings, {
                '%s/stages/bootstrap/started' % RMIT_SCHEMA: self.started,
                '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA: str(self.bootstrapped_nodes),
                '%s/system/id' % RMIT_SCHEMA: 0,
                '%s/stages/create/created_nodes' % RMIT_SCHEMA: self.created_nodes
                })
        #todo: move id to hrmc parent subclass parent?? may be not needed
        running_created_nodes = [x for x in self.created_nodes if x[3] == 'running']
        logger.debug('running created_nodes=%s' % running_created_nodes)
        if self.bootstrapped_nodes and len(self.bootstrapped_nodes) == len(running_created_nodes):
            setvals(run_settings, {
                '%s/stages/bootstrap/bootstrap_done' % RMIT_SCHEMA: 1})
        return run_settings









