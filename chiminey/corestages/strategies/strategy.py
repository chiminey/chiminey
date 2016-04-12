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

from chiminey import messages
from chiminey.runsettings import update, SettingNotFoundException, getval
from django.conf import settings as django_settings


RMIT_SCHEMA = django_settings.SCHEMA_PREFIX

class Strategy(object):
    def get_iteration_id(self, run_settings):
        try:
            return int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError):
            return 0

    def set_create_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
               '%s/system/contextid' % RMIT_SCHEMA
               )

    def create_resource(self, local_settings):
        group_id = 'UNKNOWN'
        created_nodes = []
        messages.warn_context(local_settings['contextid'], "warn: no compute resources are created")
        return group_id, created_nodes

    def set_bootstrap_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
           '%s/system/contextid' % RMIT_SCHEMA,
           '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
           )

    def start_multi_bootstrap_task(self, settings, relative_path_suffix):
        pass

    def complete_bootstrap(self, bootstrap_class, local_settings):
        pass

    def set_schedule_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
           '%s/system/contextid' % RMIT_SCHEMA,
           '%s/stages/setup/payload_destination' % RMIT_SCHEMA,
           )

    def start_schedule_task(self, schedule_class, run_settings, local_settings):
        schedule_class.total_processes = 1

    def complete_schedule(self, schedule_class, local_settings):
        schedule_class.total_scheduled_procs = 1

    def set_destroy_settings(self, run_settings, local_settings):
        pass

    def destroy_resource(self, destroy_class, run_settings, local_settings):
        pass

    def is_job_finished(self, wait_class, ip_address, process_id, retry_left, settings):
        pass
