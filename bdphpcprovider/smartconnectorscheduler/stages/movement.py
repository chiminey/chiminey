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


import logging
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage, UI
from bdphpcprovider.smartconnectorscheduler import hrmcstages


logger = logging.getLogger(__name__)


class MovementStage(Stage):
    """
    Moves files from one location to another
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings
        pass

    def triggered(self, context):
        """
        Return true if the directory pattern triggers this stage, or there
        has been any other error
        """
        # FIXME: Need to verify that triggered is idempotent.
        logger.debug("Movement Stage Triggered")
        logger.debug("context=%s" % context)
        if 'movement_output' in context:
            self.val = context['movement_output']
        else:
            self.val = 0
        return True

    def process(self, context):
        """ perfrom the stage operation
        """
        logger.debug("Movement Stage Processing")
        logger.debug("context=%s" % context)
        logger.debug("user_settings=%s", self.user_settings)
        source_url = context['file0']
        logger.debug("source_url=%s" % source_url)
        content = hrmcstages.get_file(source_url, self.user_settings)
        logger.debug("content=%s", content)
        dest_url = context['file1']
        logger.debug("dest_url=%s" % dest_url)
        hrmcstages.put_file(dest_url, content, self.user_settings)

    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("Movement Stage Output")
        logger.debug("context=%s" % context)
        self.val += 1
        context['movement_output'] = self.val
        return context
