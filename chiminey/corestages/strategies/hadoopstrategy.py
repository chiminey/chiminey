__author__ = 'Iman'
# Copyright (C) 2016, RMIT University

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
from chiminey import messages
from chiminey.runsettings import update
from django.conf import settings as django_settings
from chiminey.corestages.strategies import ClusterStrategy
from chiminey.platform import get_platform_settings


RMIT_SCHEMA = django_settings.SCHEMA_PREFIX
logger = logging.getLogger(__name__)


class HadoopStrategy(ClusterStrategy):
    def create_resource(self, local_settings):
        group_id = 'UNKNOWN'
        created_nodes = []
        created_nodes.append(['1', local_settings['ip_address'], 'hadoop', 'running'])
        messages.info_context(local_settings['contextid'], "1: create (%s nodes created)" % len(created_nodes))
        return group_id, created_nodes


    def complete_schedule(self, schedule_class, local_settings):
        try:
            payload_source = local_settings['payload_source']
        except IndexError:
            payload_source = ''
        if payload_source:
            super(HadoopStrategy, self).complete_schedule(schedule_class, local_settings)
        else:
            schedule_class.total_scheduled_procs = 1
            schedule_class.scheduled_nodes.append(
                ['1', local_settings['ip_address'], 'hadoop', 'running'])
            schedule_class.all_processes.append({'status': 'ready', 'retry_left': '2',
                                              'ip_address': local_settings['ip_address'],
                                              'id': str(local_settings['non_cloud_proc_id'])})
            schedule_class.current_processes.append({'status': 'ready', 'retry_left': '2',
                                              'ip_address': local_settings['ip_address'],
                                              'id': str(local_settings['non_cloud_proc_id'])})



    def set_bootstrap_settings(self, run_settings, local_settings):
        super(HadoopStrategy, self).set_bootstrap_settings(run_settings, local_settings)
        platform_url = run_settings['%s/platform/computation' % RMIT_SCHEMA]['platform_url']
        local_settings['root_path'] = '/home/%s' % (get_platform_settings(
            platform_url, local_settings['bdp_username'])['username'])
        logger.debug('out=%s' % local_settings)


    def set_schedule_settings(self, run_settings, local_settings):
        super(HadoopStrategy, self).set_schedule_settings(run_settings, local_settings)
        platform_url = run_settings['%s/platform/computation' % RMIT_SCHEMA]['platform_url']
        local_settings['root_path'] = '/home/%s' % (get_platform_settings(
            platform_url, local_settings['bdp_username'])['username'])
        logger.debug('out=%s' % local_settings)



    def start_multi_bootstrap_task(self, settings, relative_path_suffix):
        logger.debug('settings=%s' % settings)
        try:
            payload_source = settings['payload_source']
            if payload_source:
                super(HadoopStrategy, self).start_multi_bootstrap_task(settings, relative_path_suffix)
        except IndexError:
            pass

    def complete_bootstrap(self, bootstrap_class, local_settings):
        try:
            payload_source = local_settings['payload_source']
        except IndexError:
            payload_source = ''
        if payload_source:
            super(HadoopStrategy, self).complete_bootstrap(bootstrap_class, local_settings)
        else:
            bootstrap_class.bootstrapped_nodes.append(
                ['1', local_settings['ip_address'], 'hadoop', 'running'])

