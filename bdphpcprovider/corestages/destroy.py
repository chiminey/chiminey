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
from bdphpcprovider.platform import manage

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.cloudconnection import destroy_vms
from bdphpcprovider.corestages import stage

logger = logging.getLogger(__name__)

RMIT_SCHEMA = "http://rmit.edu.au/schemas"

class Destroy(stage.Stage):

    def __init__(self, user_settings=None):
        logger.debug('Destroy stage initialised')

    def is_triggered(self, run_settings):
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
        stage.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        stage.copy_settings(local_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        local_settings['bdp_username'] = run_settings[
            RMIT_SCHEMA + '/bdp_userprofile']['username']
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA+'/platform/computation/nectar/ec2_access_key')
        #smartconnector.copy_settings(local_settings, run_settings,
        #    RMIT_SCHEMA+'/platform/computation/nectar/ec2_secret_key')

        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']
        computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
        comp_pltf_settings = manage.get_platform_settings(computation_platform_url, bdp_username)
        local_settings.update(comp_pltf_settings)

        node_type = []
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/create',
            u'created_nodes'):
            stage.copy_settings(local_settings, run_settings,
                'http://rmit.edu.au/schemas/stages/create/created_nodes')
            #all_instances = managevms.get_registered_vms(
            #    local_settings, node_type=node_type)
            node_type.append('created_nodes')
        #else:
        #    all_instances = []

        #logger.debug('all_instance=%s' % all_instances)
        if node_type:
            destroy_vms(local_settings, node_types=node_type)
        else:
        #    logger.debug('No running VM instances in this context')
            logger.info('Destroy stage completed')

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/destroy',
            {})[u'run_finished'] = 1
        return run_settings
