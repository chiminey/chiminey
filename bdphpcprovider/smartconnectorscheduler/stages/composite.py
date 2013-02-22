from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
import logging
import logging.config

logger = logging.getLogger(__name__)

class ParallelStage(Stage):
    """
        A list of stages
    """

    def __unicode__(self):
        return "ParallelStage"

    def triggered(self, context):
        logger.debug("Parallel Stage Triggered")
        if 'parallel_output' in context:
            self.val = context['parallel_output']
        else:
            self.val = 0

        return True

    def process(self, context):
        logger.debug("Null Stage Processing")

        pass
        # while(True):
        #     done = 0
        #     for stage in smart_con.stages:
        #         print "Working in stage", stage
        #         if stage.triggered(context):
        #             stage.process(context)
        #             stage.output(context)
        #             done += 1
        #             #smart_con.unregister(stage)
        #             #print "Deleting stage",stage
        #             print done
        #     if done == len(smart_con.stages):
        #         break

        # while s.triggered(context):
        #     s.process(context)
        #     s.output(context)
        #     print context

    def output(self, context):
        logger.debug("Null Stage Output")
        self.val += 1
        context['parallel_output'] = self.val
        return context