from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import collect_instances, destroy_environ
from bdphpcprovider.smartconnectorscheduler import hrmcstages

import logging
logger = logging.getLogger(__name__)


class Teardown(smartconnector.Stage):

    def __init__(self, user_settings=None):
        pass

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
                    'http://rmit.edu.au/schemas/stages/teardown',
                    u'run_finished'):
                    run_finished = int(run_settings['http://rmit.edu.au/schemas/stages/teardown'][u'run_finished'])
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

        self.boto_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]

        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_source')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/setup/payload_destination')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/system/platform')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/created_nodes')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/group_id_dir')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/custom_prompt')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/cloud_sleep_interval')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/payload_cloud_dirname')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/max_seed_int')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/compile_file')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/retry_attempts')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_vm_instances')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/iseed')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/number_dimensions')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/hrmc/threshold')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_username')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/create/nectar_password')
        smartconnector.copy_settings(self.boto_settings, run_settings,
            'http://rmit.edu.au/schemas/stages/run/random_numbers')
        self.boto_settings['username'] = run_settings[
            'http://rmit.edu.au/schemas/stages/create']['nectar_username']
        self.boto_settings['password'] = run_settings[
            'http://rmit.edu.au/schemas/stages/create']['nectar_password']
        key_file = hrmcstages.retrieve_private_key(self.boto_settings,
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS][
                'nectar_private_key'])
        self.boto_settings['private_key'] = key_file
        self.boto_settings['nectar_private_key'] = key_file

        all_instances = collect_instances(self.boto_settings,
            group_id=self.group_id)
        destroy_environ(self.boto_settings, all_instances)

    def output(self, run_settings):
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/teardown',
            {})[u'run_finished'] = 1
        return run_settings
