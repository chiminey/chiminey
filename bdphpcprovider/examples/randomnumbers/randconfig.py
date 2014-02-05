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


from bdphpcprovider.corestages import Configure


class RandConfig(Configure):
    def get_results_dirname(self, run_settings, name):
        name = 'random_numbers_example%s' % self.contextid
        return name

    def copy_to_scratch_space(self, run_settings, local_settings):
        pass

    def output(self, run_settings):
        process = [{'status': 'ready', 'id': '1', 'ip_address': '118.138.241.230', 'retry_left': 1}]
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'current_processes'] = process
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'all_processes'] = process


        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/execute',
            {})[u'executed_procs'] = process
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/schedule',
            {})[u'schedule_completed'] = 1
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/system',
            {})[u'id'] = 0
        return super(RandConfig, self).output(run_settings)