from bdphpcprovider.corestages.stage import Stage

class Sleep(Stage):
    """
    Go to sleep
    """
    def __init__(self, secs):
        self.sleeptime = secs

    def is_triggered(self, context):
        # FIXME: broken because dispatch loop will never exit because
        # stage will always trigger.  Need to create return state that
        # triggers dispatch loop to end
        return True

    def process(self, context):
        pass

    def output(self, context):
        context['sleep_done'] = True
        return context
