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
import ast

logger = logging.getLogger(__name__)


class FTManager():
    def get_cleanup_nodes(self, run_settings, smartconnector):
        try:
            cleanup_nodes_str = smartconnector.get_existing_key(run_settings,
                'http://rmit.edu.au/schemas/reliability/cleanup_nodes')
            cleanup_nodes = ast.literal_eval(cleanup_nodes_str)
        except KeyError, e:
            cleanup_nodes = []
            logger.debug(e)
        return cleanup_nodes

    def flag_failed_processes(self, ip_address, process_list):
        no_failed_procs = 0
        for iterator, process in enumerate(process_list):
            if process['ip_address'] == ip_address:
                process_list[iterator]['status'] = 'failed'
                no_failed_procs += 1
        return process_list, no_failed_procs

    def collect_failed_processes(self, source, destination):
        for iterator, process in enumerate(source):
            if process['status'] == 'failed':
                destination.append(process)
        return destination
