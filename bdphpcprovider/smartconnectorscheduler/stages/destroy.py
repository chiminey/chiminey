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

from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import collect_instances, destroy_environ

logger = logging.getLogger(__name__)


class Destroy(smartconnector.Stage):

    def __init__(self, user_settings=None):
        self.user_settings = user_settings
        self.boto_settings = user_settings.copy()

    def triggered(self, run_settings):
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/create',
             u'group_id'):
            self.group_id = run_settings[
            'http://rmit.edu.au/schemas/stages/create'][u'group_id']
        else:
            logger.warn("no group_id found when expected")
            return False
        logger.debug("group_id = %s" % self.group_id)
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
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/created_nodes')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')

        all_instances = collect_instances(self.boto_settings,
            group_id=self.group_id)
        logger.debug('all_instance=%s' % all_instances)
        if all_instances:
            destroy_environ(self.boto_settings, all_instances)
        else:
            logger.debug('No running VM instances in this context')
            logger.info('Destroy stage completed')


    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/destroy',
            {})[u'run_finished'] = 1
        return run_settings
