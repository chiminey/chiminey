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

import unittest
from bdphpcprovider.reliabilityframework.ftmanager import FTManager


class TestFTManager(unittest.TestCase):

    def setUp(self):
        self.ftmanager = FTManager()

        self.all_procs = [{'status': 'failed', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '1'},
                     {'status': 'completed', 'ip_address': u'118.138.242.26', 'maximum_retry': '1', 'id': '2'},
                     {'status': 'completed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '3'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]

        self.current_procs = [{'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]

        self.executed_procs = [{'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        self.process_lists = [self.all_procs, self.current_procs, self.executed_procs]

    def tearDown(self):
        pass

    def test_collect_failed_processes(self):
        source = [{'status': 'completed', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '1'},
                  {'status': 'failed', 'ip_address': u'118.138.242.26', 'maximum_retry': 0, 'id': '2'},
                  {'status': 'running', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '3'},
                  {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'}]
        destination = []
        self.ftmanager.collect_failed_processes(source, destination)
        expected_list = [{'status': 'failed', 'ip_address': u'118.138.242.26', 'maximum_retry': 0, 'id': '2'},
                         {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'}]
        self.assertEqual(destination, expected_list)

    def test_flag_all_processes(self):
        ip_address = '118.138.242.25'
        self.ftmanager.flag_all_processes(self.process_lists, ip_address)
        expected_all_procs = [{'status': 'failed', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '1'},
                     {'status': 'completed', 'ip_address': u'118.138.242.26', 'maximum_retry': '1', 'id': '2'},
                     {'status': 'completed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '3'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        expected_current_procs = [{'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        expected_executed_procs = [{'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        self.assertEqual(self.all_procs, expected_all_procs)
        self.assertEqual(self.current_procs, expected_current_procs)
        self.assertEqual(self.executed_procs, expected_executed_procs)

    def test_flag_this_process(self):
        ip_address = '118.138.242.26'
        process_id = '5'
        self.ftmanager.flag_this_process(self.process_lists, ip_address, process_id)
        expected_all_procs = [{'status': 'failed', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '1'},
                     {'status': 'completed', 'ip_address': u'118.138.242.26', 'maximum_retry': '1', 'id': '2'},
                     {'status': 'completed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '3'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]

        expected_current_procs = [{'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]

        expected_executed_procs = [{'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        self.assertEqual(self.all_procs, expected_all_procs)
        self.assertEqual(self.current_procs, expected_current_procs)
        self.assertEqual(self.executed_procs, expected_executed_procs)


    def test_get_total_failed_processes(self):
        no_failed_procs = self.ftmanager.get_total_failed_processes(self.all_procs)
        self.assertEqual(no_failed_procs, 3)
        no_failed_procs = self.ftmanager.get_total_failed_processes(self.current_procs)
        self.assertEqual(no_failed_procs, 2)

    def test_decrease_max_retry(self):
        ip_address = '118.138.242.25'
        process_id = '4'
        self.ftmanager.decrease_max_retry(self.process_lists, ip_address, process_id)
        print self.process_lists
        expected_all_procs = [{'status': 'failed', 'ip_address': u'118.138.242.25', 'maximum_retry': '1', 'id': '1'},
                     {'status': 'completed', 'ip_address': u'118.138.242.26', 'maximum_retry': '1', 'id': '2'},
                     {'status': 'completed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '3'},
                     {'status': 'running', 'maximum_retry': 0, 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        expected_current_procs = [{'status': 'running', 'maximum_retry': 0, 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        expected_executed_procs = [{'status': 'running', 'maximum_retry': 0, 'ip_address': u'118.138.242.25', 'id': '4'},
                     {'status': 'running', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '5'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.26', 'id': '6'},
                     {'status': 'failed', 'maximum_retry': '1', 'ip_address': u'118.138.242.27', 'id': '7'}]
        self.assertEqual(self.all_procs, expected_all_procs)
        self.assertEqual(self.current_procs, expected_current_procs)
        self.assertEqual(self.executed_procs, expected_executed_procs)