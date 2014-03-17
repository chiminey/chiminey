# Copyright (C) 2014, RMIT University

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
from chiminey.corestages import Execute
from chiminey.compute import run_command


logger = logging.getLogger(__name__)

class RandExecute(Execute):
    def run_task(self, ip_address, process_id, connection_settings, run_settings):
        filename = 'rand'
        output_path = self.get_process_output_path(
            run_settings, process_id, connection_settings)
        logger.debug('output_path=%s' % output_path)
        command = "mkdir -p %s; cd %s ; python -c 'import random;" \
                  " print random.random(); print random.random()' > %s" \
                  % (output_path, output_path, filename)
        output, err = run_command(command, ip_address, connection_settings)