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
        return True

    def process(self, run_settings):
        pass

    def output(self, run_settings):
        return run_settings