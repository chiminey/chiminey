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

from chiminey.corestages import strategies
from chiminey.corestages.stage import Stage
from chiminey.runsettings import getval, setval, setvals, SettingNotFoundException
from chiminey import messages


logger = logging.getLogger(__name__)
RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Schedule(Stage):
    """
    Schedules processes on a cloud infrastructure
    """

    def __init__(self, user_settings=None):
        logger.debug('Schedule stage initialised')

    #fixme: refactor the method
    #fixme: reschedule should be based on running_bootstrapped_nodes .. it already is
    def is_triggered(self, run_settings):
        try:
            self.created_nodes = ast.literal_eval(getval(run_settings,
                                 '%s/stages/create/created_nodes' % RMIT_SCHEMA))
            running_created_nodes = [x for x in self.created_nodes if str(x[3]) == 'running']
            logger.debug('running_created_nodes=%s' % running_created_nodes)
            if len(running_created_nodes) == 0:
                return False
        except (SettingNotFoundException, ValueError) as e:
            logger.debug(e)
            return False
        try:
            bootstrap_done = int(getval(run_settings,
                                 '%s/stages/bootstrap/bootstrap_done' % RMIT_SCHEMA))
            if not bootstrap_done:
                return False
        except (SettingNotFoundException, ValueError) as e:
            logger.debug(e)
            return False
        try:
            self.bootstrapped_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/bootstrap/bootstrapped_nodes' % RMIT_SCHEMA))
            if len(self.bootstrapped_nodes) == 0:
                return False
        except (SettingNotFoundException, ValueError) as e:
            return False
        try:
            reschedule_str = getval(run_settings, '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA)
            # reschedule_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'procs_2b_rescheduled']
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
        except SettingNotFoundException, e:
            # FIXME: when is procs_2b_rescheduled set?
            logger.debug(e)
            self.procs_2b_rescheduled = []

        if self.procs_2b_rescheduled:
            #self.trigger_reschedule(run_settings)
            try:
                self.total_rescheduled_procs = getval(run_settings, '%s/stages/schedule/total_rescheduled_procs' % RMIT_SCHEMA)
                # self.total_rescheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_rescheduled_procs']
            except SettingNotFoundException, e:
                self.total_rescheduled_procs = 0
            self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
            if (self.total_procs_2b_rescheduled == self.total_rescheduled_procs) and self.total_rescheduled_procs:
                return False
        else:
            try:
                self.total_scheduled_procs = getval(run_settings, '%s/stages/schedule/total_scheduled_procs' % RMIT_SCHEMA)
                # self.total_scheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_scheduled_procs']
            except SettingNotFoundException:
                self.total_scheduled_procs = 0

            try:
                total_procs = int(getval(run_settings, '%s/stages/schedule/total_processes' % RMIT_SCHEMA))
                # total_procs = int(run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_processes'])
                if total_procs:
                    if total_procs == self.total_scheduled_procs:
                        return False
            except SettingNotFoundException, e:
                logger.debug(e)
            except ValueError, e:
                logger.error(e)

        try:
            scheduled_str = getval(run_settings, '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA)

            # scheduled_str = smartconnectorscheduler.get_existing_key(
            #     run_settings,
            #     'http://rmit.edu.au/schemas/stages/schedule/scheduled_nodes')

            self.scheduled_nodes = ast.literal_eval(scheduled_str)
            #current_processes_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
            #self.current_processes = ast.literal_eval(current_processes_str)
        except SettingNotFoundException, e:
            self.scheduled_nodes = []
        except ValueError, e:
            logger.error(e)
            self.scheduled_nodes = []

        try:
            rescheduled_str = getval(run_settings, '%s/stages/schedule/rescheduled_nodes' % RMIT_SCHEMA)
            # rescheduled_str = smartconnectorscheduler.get_existing_key(
            #     run_settings,
            #     'http://rmit.edu.au/schemas/stages/schedule/rescheduled_nodes')
            self.rescheduled_nodes = ast.literal_eval(rescheduled_str)
        except SettingNotFoundException, e:
            self.rescheduled_nodes = []
        except ValueError, e:
            logger.error(e)
            self.rescheduled_nodes = []

        try:
            current_processes_str = getval(run_settings, '%s/stages/schedule/current_processes' % RMIT_SCHEMA)
            # current_processes_str = smartconnectorscheduler.get_existing_key(
            #     run_settings,
            #     'http://rmit.edu.au/schemas/stages/schedule/current_processes')
            #self.scheduled_nodes = ast.literal_eval(scheduled_str)
            #current_processes_str = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'current_processes']
            self.current_processes = ast.literal_eval(current_processes_str)
        except SettingNotFoundException, e:
            self.current_processes = []
        except ValueError, e:
            logger.error(e)
            self.current_processes = []

        try:
            all_processes_str = getval(run_settings, '%s/stages/schedule/all_processes' % RMIT_SCHEMA)
            # all_processes_str = smartconnectorscheduler.get_existing_key(run_settings,
            # 'http://rmit.edu.au/schemas/stages/schedule/all_processes')
            self.all_processes = ast.literal_eval(all_processes_str)
        except SettingNotFoundException:
            self.all_processes = []
        except ValueError, e:
            logger.error(e)
            self.all_processes = []

        return True

    def trigger_schedule(self, run_settings):

        try:
            self.total_scheduled_procs = getval(run_settings, '%s/stages/schedule/total_scheduled_procs' % RMIT_SCHEMA)
            # self.total_scheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_scheduled_procs']
        except SettingNotFoundException:
            self.total_scheduled_procs = 0

        try:
            total_procs = int(getval(run_settings, '%s/stages/schedule/total_processes' % RMIT_SCHEMA))
            # total_procs = int(run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_processes'])
            if total_procs:
                if total_procs == self.total_scheduled_procs:
                    return False
        except SettingNotFoundException, e:
            logger.debug(e)

    def trigger_reschedule(self, run_settings):

        try:
            self.total_rescheduled_procs = getval(run_settings, '%s/stages/schedule/total_rescheduled_procs' % RMIT_SCHEMA)
            # self.total_rescheduled_procs = run_settings['http://rmit.edu.au/schemas/stages/schedule'][u'total_rescheduled_procs']
        except SettingNotFoundException:
            self.total_rescheduled_procs = 0
        self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
        if self.total_procs_2b_rescheduled == self.total_rescheduled_procs:
            return False

    def process(self, run_settings):
        logger.debug("schedule processing")
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
            self.strategy.set_schedule_settings(run_settings, local_settings)
            local_settings.update(comp_pltf_settings)
        except SettingNotFoundException, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        try:
            self.started = int(getval(run_settings, '%s/stages/schedule/schedule_started' % RMIT_SCHEMA))
        except SettingNotFoundException:
            self.started = 0
        except ValueError, e:
            logger.error(e)

        logger.debug("started=%s" % self.started)
        logger.debug('Schedule there')
        if not self.started:
            logger.debug("initial run")
            try:
                self.schedule_index = int(getval(run_settings, '%s/stages/schedule/schedule_index' % RMIT_SCHEMA))
            except SettingNotFoundException:
                self.schedule_index = 0
            except ValueError, e:
                logger.error(e)
                self.schedule_index = 0
            logger.debug('schedule_index=%d' % self.schedule_index)
            self.strategy.start_schedule_task(self, run_settings, local_settings)
        else:
            self.strategy.complete_schedule(self, local_settings)

    def output(self, run_settings):

        setvals(run_settings, {
                '%s/stages/schedule/scheduled_nodes' % RMIT_SCHEMA: str(self.scheduled_nodes),
                '%s/stages/schedule/rescheduled_nodes' % RMIT_SCHEMA: str(self.rescheduled_nodes),
                '%s/stages/schedule/all_processes' % RMIT_SCHEMA: str(self.all_processes),
                '%s/stages/schedule/current_processes' % RMIT_SCHEMA: str(self.current_processes)
                })
        if not self.started:

            setvals(run_settings, {
                    '%s/stages/schedule/schedule_started' % RMIT_SCHEMA: 1,
                    '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA: self.procs_2b_rescheduled
                    })
            if not self.procs_2b_rescheduled:

                setvals(run_settings, {
                        '%s/stages/schedule/total_processes' % RMIT_SCHEMA: str(self.total_processes),
                        '%s/stages/schedule/schedule_index' % RMIT_SCHEMA: self.schedule_index
                        })
        else:
            if self.procs_2b_rescheduled:
                setval(run_settings,
                        '%s/stages/schedule/total_rescheduled_procs' % RMIT_SCHEMA,
                        self.total_rescheduled_procs)
                if self.total_rescheduled_procs == len(self.procs_2b_rescheduled):
                    setvals(run_settings, {
                        '%s/stages/schedule/schedule_completed' % RMIT_SCHEMA: 1,
                        '%s/stages/schedule/procs_2b_rescheduled' % RMIT_SCHEMA: [],
                        '%s/stages/schedule/total_rescheduled_procs' % RMIT_SCHEMA: 0,
                        '%s/stages/schedule/rescheduled_nodes' % RMIT_SCHEMA: [],
                        })
            else:
                setval(run_settings,
                       '%s/stages/schedule/total_scheduled_procs' % RMIT_SCHEMA,
                       self.total_scheduled_procs)
                if self.total_scheduled_procs == len(self.current_processes):
                    setval(run_settings,
                           '%s/stages/schedule/schedule_completed' % RMIT_SCHEMA,
                           1)
        return run_settings
