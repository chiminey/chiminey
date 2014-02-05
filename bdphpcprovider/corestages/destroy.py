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

from bdphpcprovider.runsettings import getval, setvals, getvals, update, SettingNotFoundException

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

        local_settings = getvals(run_settings, models.UserProfile.PROFILE_SCHEMA_NS)
        # local_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        update(local_settings, run_settings,
               #'%s/system/platform' % RMIT_SCHEMA,
               '%s/stages/create/cloud_sleep_interval' % RMIT_SCHEMA)
        # smartconnector.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/system/platform')
        # smartconnector.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
        # local_settings['bdp_username'] = run_settings[
        #     RMIT_SCHEMA + '/bdp_userprofile']['username']

        computation_platform_url = getval(run_settings, '%s/platform/computation/platform_url' % RMIT_SCHEMA)
        # computation_platform_url = run_settings['http://rmit.edu.au/schemas/platform/computation']['platform_url']
        comp_pltf_settings = manage.get_platform_settings(computation_platform_url, local_settings['bdp_username'])
        local_settings.update(comp_pltf_settings)

        node_type = []

        try:
            if getvals(run_settings, '%s/stages/create'):
                update(local_settings,
                       run_settings,
                       '%s/stages/create/created_nodes' % RMIT_SCHEMA)
                node_type.append('created_nodes')

        except SettingNotFoundException:
            pass

        # if self._exists(run_settings,
        #     'http://rmit.edu.au/schemas/stages/create',
        #     u'created_nodes'):
        #     smartconnector.copy_settings(local_settings, run_settings,
        #         'http://rmit.edu.au/schemas/stages/create/created_nodes')
        #     #all_instances = managevms.get_registered_vms(
        #     #    local_settings, node_type=node_type)
        #     node_type.append('created_nodes')
        # #else:
        # #    all_instances = []


        #logger.debug('all_instance=%s' % all_instances)
        if node_type:
            destroy_vms(local_settings, node_types=node_type)
        else:
        #    logger.debug('No running VM instances in this context')
            logger.info('Destroy stage completed')

    def output(self, run_settings):
        setvals(run_settings, {
            '%s/stages/destroy/run_finished' % RMIT_SCHEMA: 1
               })
        return run_settings
