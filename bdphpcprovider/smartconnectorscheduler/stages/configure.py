from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
from bdphpcprovider.smartconnectorscheduler.filesystem import FileSystem, DataObject
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_settings
from bdphpcprovider.smartconnectorscheduler.errors import ContextKeyMissing

import logging
logger = logging.getLogger(__name__)


class Configure(Stage, UI):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def __init__(self, user_settings=None):
        self.user_settings = user_settings

    def triggered(self, run_settings):
        if self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/configure', 'configure_done'):
            return False
        return True

    def process(self, run_settings):
        pass

    def output(self, run_settings):

        if not self._exists(run_settings, 'http://rmit.edu.au/schemas/stages/configure'):
            run_settings['http://rmit.edu.au/schemas/stages/configure'] = {}
        run_settings['http://rmit.edu.au/schemas/stages/configure'][u'configure_done'] = True

        return run_settings
