import logging
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI


logger = logging.getLogger(__name__)


# This stage doesn't do any thing except register its execution
class NullStage(Stage):
    def __init__(self):
        pass

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that triggered is idempotent.
        logger.debug("Null Stage Triggered")
        logger.debug("context=%s" % context)
        if 'null_output' in context:
            self.val = context['null_output']
        else:
            self.val = 0
        return True

    def process(self, context):
        """ perfrom the stage operation
        """
        logger.debug("Null Stage Processing")
        logger.debug("context=%s" % context)


    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Null Stage Processing")
        logger.debug("context=%s" % context)
        self.val += 1
        context['null_output'] = self.val
        return context
