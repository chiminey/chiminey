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


import logging
import ast
import os

from bdphpcprovider.smartconnectorscheduler import smartconnector, models, platform
from bdphpcprovider.smartconnectorscheduler.botocloudconnector \
    import collect_instances, destroy_environ

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

class Destroy(smartconnector.Stage):

    def __init__(self, user_settings=None):
        logger.debug('Destroy stage initialised')

    def triggered(self, run_settings):
        try:
            cleanup_nodes_str = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/reliability/cleanup_nodes')
            self.cleanup_nodes = ast.literal_eval(cleanup_nodes_str)
            if self.cleanup_nodes:
                return True
        except KeyError, e:
            self.cleanup_nodes = []
            logger.debug(e)

        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/converge',
            u'converged'):
            converged = int(run_settings['http://rmit.edu.au/schemas/stages/converge'][u'converged'])
            logger.debug("converged=%s" % converged)
            if converged:
                if self._exists(run_settings,
                    'http://rmit.edu.au/schemas/stages/destroy',
                    u'run_finished'):
                    run_finished = int(run_settings['http://rmit.edu.au/schemas/stages/destroy'][u'run_finished'])
                    return not run_finished
                else:
                    return True
        return False
        # if 'converged' in self.settings:
        #     if self.settings['converged']:
        #         if not 'run_finished' in self.settings:
        #             return True
        # return False

    def process(self, run_settings):
        local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA+'/platform/computation/nectar/ec2_access_key')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA+'/platform/computation/nectar/ec2_secret_key')

        comp_pltf_schema = run_settings['http://rmit.edu.au/schemas/platform/computation']['namespace']
        comp_pltf_settings = run_settings[comp_pltf_schema]
        platform.update_platform_settings(comp_pltf_schema, comp_pltf_settings)
        local_settings.update(comp_pltf_settings)

        node_type = 'created_nodes'
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/create',
            u'created_nodes'):
            smartconnector.copy_settings(local_settings, run_settings,
                'http://rmit.edu.au/schemas/stages/create/created_nodes')
            all_instances = collect_instances(local_settings,
                registered=True, node_type=node_type)
        else:
            all_instances = []

        if self.cleanup_nodes:
            smartconnector.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/reliability/cleanup_nodes')
            node_type = 'cleanup_nodes'
            all_instances.extend(collect_instances(local_settings,
            registered=True, node_type=node_type))

        logger.debug('all_instance=%s' % all_instances)
        if all_instances:
            destroy_environ(local_settings, all_instances)
        else:
            logger.debug('No running VM instances in this context')
            logger.info('Destroy stage completed')

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/destroy',
            {})[u'run_finished'] = 1

        if self.cleanup_nodes:
            run_settings.setdefault(
            'http://rmit.edu.au/schemas/reliability', {})[u'cleanup_nodes'] = []

        return run_settings
