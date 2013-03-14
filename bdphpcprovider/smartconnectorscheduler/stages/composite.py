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


from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
import logging
import logging.config

logger = logging.getLogger(__name__)


class ParallelStage(Stage):
    """
        A list of stages
    """
    def __init__(self, user_settings=None):
        pass

    def __unicode__(self):
        return "ParallelStage"

    def triggered(self, context):
        logger.debug("Parallel Stage Triggered")
        if 'parallel_output' in context:
            self.val = context['parallel_output']
        else:
            self.val = 0

        # parallel_index indicates which of a set of identical nullstages in
        # a composite have been triggered.  It is must be set via passed
        # directive argument.  FIXME: this should be a smart connector specific
        # parameter set during directive definition

        if 'parallel_index' in context:
            self.parallel_index = context['parallel_index']
        else:
            self.parallel_index = context['parallel_number']

        if self.parallel_index:
            return True

        return False

    def process(self, context):
        logger.debug("Parallel Stage Processing")
        pass

    def output(self, context):
        logger.debug("Parallel Stage Output")
        self.val += 1
        context['parallel_output'] = self.val

        self.parallel_index -= 1
        context['parallel_index'] = self.parallel_index


        return context
