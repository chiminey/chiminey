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
        logger.debug("context=%s" % context)

        if self._exists(context, u'http://rmit.edu.au/schemas/stages/parallel/testing', u'output'):
            self.val = context[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'output']
        else:
            self.val = 0

        if self._exists(context, u'http://rmit.edu.au/schemas/stages/parallel/testing', u'index'):
            self.parallel_index = context[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'index']
        else:
            try:
                self.parallel_index = context[u'http://rmit.edu.au/schemas/smartconnector1/create'][u'parallel_number']
            except KeyError:
                logger.error("context%s" % context)
                raise

        if self.parallel_index:
            return True

        return False

    def process(self, context):
        logger.debug("Parallel Stage Processing")
        pass

    def output(self, context):
        logger.debug("Parallel Stage Output")

        if not self._exists(context, u'http://rmit.edu.au/schemas/stages/parallel/testing'):
            context[u'http://rmit.edu.au/schemas/stages/parallel/testing'] = {}

        self.val += 1
        context[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'output'] = self.val

        self.parallel_index -= 1
        context[u'http://rmit.edu.au/schemas/stages/parallel/testing'][u'index'] = self.parallel_index
        return context
