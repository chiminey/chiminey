from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_run_settings, update_key
from bdphpcprovider.smartconnectorscheduler.botocloudconnector import collect_instances, destroy_environ

import logging
logger = logging.getLogger(__name__)


class Teardown(Stage):
    def triggered(self, context):
        self.settings = get_run_settings(context)
        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]
        logger.debug("group_id = %s" % self.group_id)

        if 'converged' in self.settings:
            if self.settings['converged']:
                if not 'run_finished' in self.settings:
                    return True
        return False

    def process(self, context):
        all_instances = collect_instances(self.settings,
            group_id=self.group_id)
        destroy_environ(self.settings, all_instances)

    def output(self, context):
        update_key('run_finished', True, context)
        return context

