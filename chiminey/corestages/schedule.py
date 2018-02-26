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
import datetime

from chiminey.corestages import strategies
from chiminey.corestages.stage import Stage
from chiminey.runsettings import getval, setval, setvals, SettingNotFoundException
from chiminey import messages
from django.conf import settings as django_settings
from chiminey.smartconnectorscheduler import jobs
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)
from django.conf import settings as django_settings


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
                                 '%s/stages/create/created_nodes' % django_settings.SCHEMA_PREFIX))
            running_created_nodes = [x for x in self.created_nodes if str(x[3]) == 'running']
            logger.debug('running_created_nodes=%s' % running_created_nodes)
            if len(running_created_nodes) == 0:
                return False
        except (SettingNotFoundException, ValueError) as e:
            logger.debug(e)
            return False
        try:
            bootstrap_done = int(getval(run_settings,
                                 '%s/stages/bootstrap/bootstrap_done' % django_settings.SCHEMA_PREFIX))
            if not bootstrap_done:
                return False
        except (SettingNotFoundException, ValueError) as e:
            logger.debug(e)
            return False
        try:
            self.bootstrapped_nodes = ast.literal_eval(getval(
                run_settings, '%s/stages/bootstrap/bootstrapped_nodes' % django_settings.SCHEMA_PREFIX))
            if len(self.bootstrapped_nodes) == 0:
                return False
        except (SettingNotFoundException, ValueError) as e:
            return False
        try:
            reschedule_str = getval(run_settings, '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX)
            self.procs_2b_rescheduled = ast.literal_eval(reschedule_str)
        except SettingNotFoundException, e:
            # FIXME: when is procs_2b_rescheduled set?
            logger.debug(e)
            self.procs_2b_rescheduled = []

        if self.procs_2b_rescheduled:
            #self.trigger_reschedule(run_settings)
            try:
                self.total_rescheduled_procs = getval(run_settings, '%s/stages/schedule/total_rescheduled_procs' % django_settings.SCHEMA_PREFIX)
            except SettingNotFoundException, e:
                self.total_rescheduled_procs = 0
            self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
            if (self.total_procs_2b_rescheduled == self.total_rescheduled_procs) and self.total_rescheduled_procs:
                return False
        else:
            try:
                self.total_scheduled_procs = getval(run_settings, '%s/stages/schedule/total_scheduled_procs' % django_settings.SCHEMA_PREFIX)
            except SettingNotFoundException:
                self.total_scheduled_procs = 0

            try:
                total_procs = int(getval(run_settings, '%s/stages/schedule/total_processes' % django_settings.SCHEMA_PREFIX))
                if total_procs:
                    if total_procs == self.total_scheduled_procs:
                        return False
            except SettingNotFoundException, e:
                logger.debug(e)
            except ValueError, e:
                logger.error(e)

        try:
            scheduled_str = getval(run_settings, '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX)
            self.scheduled_nodes = ast.literal_eval(scheduled_str)
        except SettingNotFoundException, e:
            self.scheduled_nodes = []
        except ValueError, e:
            logger.error(e)
            self.scheduled_nodes = []
        try:
            rescheduled_str = getval(run_settings, '%s/stages/schedule/rescheduled_nodes' % django_settings.SCHEMA_PREFIX)
            self.rescheduled_nodes = ast.literal_eval(rescheduled_str)
        except SettingNotFoundException, e:
            self.rescheduled_nodes = []
        except ValueError, e:
            logger.error(e)
            self.rescheduled_nodes = []

        try:
            current_processes_str = getval(run_settings, '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX)
            self.current_processes = ast.literal_eval(current_processes_str)
        except SettingNotFoundException, e:
            self.current_processes = []
        except ValueError, e:
            logger.error(e)
            self.current_processes = []

        try:
            all_processes_str = getval(run_settings, '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX)
            self.all_processes = ast.literal_eval(all_processes_str)
        except SettingNotFoundException:
            self.all_processes = []
        except ValueError, e:
            logger.error(e)
            self.all_processes = []

        return True

    def trigger_schedule(self, run_settings):

        try:
            self.total_scheduled_procs = getval(run_settings, '%s/stages/schedule/total_scheduled_procs' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            self.total_scheduled_procs = 0

        try:
            total_procs = int(getval(run_settings, '%s/stages/schedule/total_processes' % django_settings.SCHEMA_PREFIX))
            if total_procs:
                if total_procs == self.total_scheduled_procs:
                    return False
        except SettingNotFoundException, e:
            logger.debug(e)

    def trigger_reschedule(self, run_settings):

        try:
            self.total_rescheduled_procs = getval(run_settings, '%s/stages/schedule/total_rescheduled_procs' % django_settings.SCHEMA_PREFIX)
        except SettingNotFoundException:
            self.total_rescheduled_procs = 0
        self.total_procs_2b_rescheduled = len(self.procs_2b_rescheduled)
        if self.total_procs_2b_rescheduled == self.total_rescheduled_procs:
            return False

    def process(self, run_settings):
        logger.debug("schedule processing")
        try:
            self.schedule_stage_start_time = str(getval(run_settings, '%s/stages/schedule/schedule_stage_start_time' % django_settings.SCHEMA_PREFIX))
            logger.debug("WWWWW schedule stage start time : %s " % (self.schedule_stage_start_time))
        except SettingNotFoundException:
            self.schedule_stage_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("WWWWW schedule stage start time new : %s " % (self.schedule_stage_start_time))
        except ValueError, e:
            logger.error(e)
      
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
        local_settings = {}
        try:
            self.strategy.set_schedule_settings(run_settings, local_settings)
            local_settings.update(comp_pltf_settings)
        except SettingNotFoundException, e:
            logger.error(e)
            messages.error(run_settings, e)
            return
        try:
            self.started = int(getval(run_settings, '%s/stages/schedule/schedule_started' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.started = 0
        except ValueError, e:
            logger.error(e)

        try:
            self.schedule_start_time = str(getval(run_settings, '%s/stages/schedule/schedule_start_time' % django_settings.SCHEMA_PREFIX))
        except SettingNotFoundException:
            self.schedule_start_time = ''
        except ValueError, e:
            logger.error(e)

        logger.debug("started=%s" % self.started)
        logger.debug("schedule_start_time=%s" % self.schedule_start_time)
        logger.debug('Schedule there')
        if not self.started:
            logger.debug("initial run")
            try:
                self.schedule_index = int(getval(run_settings, '%s/stages/schedule/schedule_index' % django_settings.SCHEMA_PREFIX))
            except SettingNotFoundException:
                self.schedule_index = 0
            except ValueError, e:
                logger.error(e)
                self.schedule_index = 0

            logger.debug('schedule_index=%d' % self.schedule_index)
            self.schedule_start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.strategy.start_schedule_task(self, run_settings, local_settings)
        else:
            self.strategy.complete_schedule(self, local_settings)

        try:
            self.schedule_stage_end_time = str(getval(run_settings, '%s/stages/schedule/schedule_stage_end_time' % django_settings.SCHEMA_PREFIX))
            logger.debug("WWWWW schedule stage end time : %s " % (self.schedule_stage_end_time))
        except SettingNotFoundException:
            self.schedule_stage_end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("WWWWW schedule stage end time new : %s " % (self.schedule_stage_end_time))
        except ValueError, e:
            logger.error(e)

    def output(self, run_settings):
        schedstg_start_time=datetime.datetime.strptime(self.schedule_stage_start_time,"%Y-%m-%d  %H:%M:%S")
        schedstg_end_time=datetime.datetime.strptime(self.schedule_stage_end_time,"%Y-%m-%d  %H:%M:%S")
        total_schedstg_time=schedstg_end_time - schedstg_start_time
        total_time_schedule_stage = str(total_schedstg_time)
        logger.debug('run_settings=%s' % run_settings)
        setvals(run_settings, {
                '%s/stages/schedule/scheduled_nodes' % django_settings.SCHEMA_PREFIX: str(self.scheduled_nodes),
                '%s/stages/schedule/rescheduled_nodes' % django_settings.SCHEMA_PREFIX: str(self.rescheduled_nodes),
                '%s/stages/schedule/all_processes' % django_settings.SCHEMA_PREFIX: str(self.all_processes),
                '%s/stages/schedule/current_processes' % django_settings.SCHEMA_PREFIX: str(self.current_processes)
                })
        if not self.started:
            #schedule_start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            setvals(run_settings, {
                    '%s/stages/schedule/schedule_started' % django_settings.SCHEMA_PREFIX: 1,
                    '%s/stages/schedule/schedule_start_time' % django_settings.SCHEMA_PREFIX: self.schedule_start_time,
                    '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX: self.procs_2b_rescheduled
                    })
            if not self.procs_2b_rescheduled:

                setvals(run_settings, {
                        '%s/stages/schedule/total_processes' % django_settings.SCHEMA_PREFIX: str(self.total_processes),
                        '%s/stages/schedule/schedule_index' % django_settings.SCHEMA_PREFIX: self.schedule_index
                        })
        else:
            if self.procs_2b_rescheduled:
                setval(run_settings,
                        '%s/stages/schedule/total_rescheduled_procs' % django_settings.SCHEMA_PREFIX,
                        self.total_rescheduled_procs)
                if self.total_rescheduled_procs == len(self.procs_2b_rescheduled):
                    schedule_complete_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sched_start_time=datetime.datetime.strptime(self.schedule_start_time,"%Y-%m-%d  %H:%M:%S")
                    sched_comp_time=datetime.datetime.strptime(schedule_complete_time,"%Y-%m-%d  %H:%M:%S")
                    total_sched_time=sched_comp_time - sched_start_time
                    total_schedule_time = str(total_sched_time)
                    setvals(run_settings, {
                        '%s/stages/schedule/schedule_completed' % django_settings.SCHEMA_PREFIX: 1,
                        '%s/stages/schedule/procs_2b_rescheduled' % django_settings.SCHEMA_PREFIX: [],
                        '%s/stages/schedule/total_rescheduled_procs' % django_settings.SCHEMA_PREFIX: 0,
                        '%s/stages/schedule/rescheduled_nodes' % django_settings.SCHEMA_PREFIX: [],
                        '%s/stages/schedule/schedule_start_time' % django_settings.SCHEMA_PREFIX: self.schedule_start_time,
                        '%s/stages/schedule/schedule_complete_time' % django_settings.SCHEMA_PREFIX: schedule_complete_time,
                        '%s/stages/schedule/total_schedule_time' % django_settings.SCHEMA_PREFIX: total_schedule_time,
                        '%s/stages/schedule/schedule_stage_start_time' % django_settings.SCHEMA_PREFIX: self.schedule_stage_start_time,
                        '%s/stages/schedule/schedule_stage_end_time' % django_settings.SCHEMA_PREFIX: self.schedule_stage_end_time,
                        '%s/stages/schedule/total_time_schedule_stage' % django_settings.SCHEMA_PREFIX: total_time_schedule_stage,

                        })
            else:
                setval(run_settings,
                       '%s/stages/schedule/total_scheduled_procs' % django_settings.SCHEMA_PREFIX,
                       self.total_scheduled_procs)
                if self.total_scheduled_procs == len(self.current_processes):
                    schedule_complete_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sched_start_time=datetime.datetime.strptime(self.schedule_start_time,"%Y-%m-%d  %H:%M:%S")
                    sched_comp_time=datetime.datetime.strptime(schedule_complete_time,"%Y-%m-%d  %H:%M:%S")
                    total_sched_time=sched_comp_time - sched_start_time
                    total_schedule_time = str(total_sched_time)
                    setvals(run_settings, {
                        '%s/stages/schedule/schedule_completed' % django_settings.SCHEMA_PREFIX: 1,
                        '%s/stages/schedule/schedule_start_time' % django_settings.SCHEMA_PREFIX: self.schedule_start_time,
                        '%s/stages/schedule/schedule_complete_time' % django_settings.SCHEMA_PREFIX: schedule_complete_time,
                        '%s/stages/schedule/total_schedule_time' % django_settings.SCHEMA_PREFIX: total_schedule_time,
                        '%s/stages/schedule/schedule_stage_start_time' % django_settings.SCHEMA_PREFIX: self.schedule_stage_start_time,
                        '%s/stages/schedule/schedule_stage_end_time' % django_settings.SCHEMA_PREFIX: self.schedule_stage_end_time,
                        '%s/stages/schedule/total_time_schedule_stage' % django_settings.SCHEMA_PREFIX: total_time_schedule_stage,
                         })
        return run_settings
