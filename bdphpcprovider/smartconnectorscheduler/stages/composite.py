from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI

class ParallelStage(Stage):
    """
        A list of stages
    """

    def __unicode__(self):
        return "ParallelStage"

    def triggered(self, context):
        return True

    def process(self, context):
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
        return context