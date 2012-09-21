
# Contains the specific connectors and stages for HRMC


import logging
import logging.config
import json
logger = logging.getLogger(__name__)


from smartconnector import Stage


class FileElement():
    # Assume that whole file is contained in one big string
    # as it makes json parsing easier

    def __init__(self):
        self.line = ""

    def create(self,line):
        self.line = line

    def retrieve(self):
        return self.line


class FileSystem(object):

    def __init__(self):
        self.fs = {}

    def create(self, name, felem):
        self.fs[name] = felem

    def retrieve(self, name):
        return self.fs[name]

    def update(self, name, felem):
        self.fs[name] = felem

    def delete(self):
        self.fs.delete(felem)
        pass

    def __str__(self):
        return "%s" % self.fs


class Setup(Stage):

    def triggered(self, context):
        try:
            fsys = context['filesys']
        except KeyError,e:
            return False
        logger.debug("fsys= %s" % fsys)
        try:
            config = fsys.retrieve("/config.sys")
        except KeyError,e:
            return False
        logger.debug("config= %s" % config)

        settings_text = config.retrieve()

        logger.debug("settings_text= %s" % settings_text)

        self.settings = json.loads(settings_text)
        self.group_id = self.settings['group_id']

        logger.debug("settings = %s" % self.settings)
        logger.debug("group_id = %s" % self.group_id)

        return True
        # triggered if the state of the VMS has been established.

    def process(self, context):

        setup_multi_task(self.group_id, self.settings)
        pass

    def output(self, context):
        pass
