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

import os
import tempfile
import unittest
from pprint import pformat
import logging
import logging.config

from nose.plugins.skip import SkipTest


from django.contrib.auth.models import User
from django import test as djangotest
from django.conf import settings
from bdphpcprovider.smartconnectorscheduler.management.commands import view
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector

from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
logger = logging.getLogger(__name__)

def error(e):
    raise


class TestPBS(unittest.TestCase):
    """
    Test functions that manipulate BDPURLS
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_pbs(self):
        self.assertTrue(False)

