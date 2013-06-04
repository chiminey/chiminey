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
import logging
import logging.config
import requests
from requests.auth import HTTPBasicAuth
import json

from django.conf import settings
from nose.plugins.skip import SkipTest

from django.contrib.auth.models import User
from django import test as djangotest

from bdphpcprovider.smartconnectorscheduler.management.commands import view
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException

logger = logging.getLogger(__name__)


class TestTardisAPI(unittest.TestCase):
    """
    Communicate with external mytardis api to push results
    """

    def setUp(self):

        models.Platform.objects.get_or_create(name='local',
            root_path="/var/cloudenabling/remotesys")

        self.settings = {'mytardis_user': 'mytardis',
            'mytardis_password': 'dtofaamdtofaam',
            'mytardis_host': '115.146.85.142'}

        file_info = (
            ('test/sweep01/run02/output_1/node01/file1.txt', "content1"),
            ('test/sweep01/run02/output_1/node02/file2.txt', "content2"),
            ('test/sweep01/run02/output_2/node01/HRMC.inp_values',
                '{"run_counter": 4, "generator_counter": 2}'),
            ('test/sweep01/run02/output_3/node01/foo/file4.txt', "content4"),
            ('test/sweep01/run02/output_3/node02/file5.txt', "content5"),
            )

        for fpath, content in file_info:
            dest_url = smartconnector.get_url_with_pkey(self.settings,
                fpath, is_relative_path=True)
            hrmcstages.put_file(dest_url, content.encode('utf-8'))

    def tearDown(self):
        pass

    def test_post_experiment(self):

        if not settings.TEST_MYTARDIS_IP:
            raise SkipTest


        tardis_host = settings.TEST_MYTARDIS_IP

        tardis_user = settings.TEST_MTARDIS_USER
        tardis_pass = settings.TEST_MYTARDIS_PASSWORD

        tardis_host_url = "http://%s" % tardis_host
        tardis_url = "%s/api/v1/experiment/?format=json" % tardis_host_url
        headers = {'content-type': 'application/json'}
        data = json.dumps({
            'title': 'test experiment',
            'description': 'some test repo'})
        print data
        r = requests.post(tardis_url, data=data, headers=headers, auth=(tardis_user, tardis_pass))
        print r.json
        print r.text
        print r.headers

        header_location = r.headers['location']

        print header_location

        header_location = header_location[len(tardis_host_url):]

        print header_location

        tardis_url = "%s/api/v1/dataset/?format=json" % tardis_host_url
        headers = {'content-type': 'application/json'}
        data = json.dumps({
            'title': 'test dataset',
            'experiments': [header_location],
            'description': 'some test dataset',
            "parameter_sets": [{
                    "schema": "http://rmit.edu.au/schemas/hrmcdataset",
                    "parameters": []
                   }]
                })
        print data
        r = requests.post(tardis_url, data=data, headers=headers, auth=(tardis_user, tardis_pass))
        print r.json
        print r.text
        print r.headers

        header_location = r.headers['location']

        print header_location

        header_location = header_location[len(tardis_host_url):]

        print header_location

        filename = "/opt/cloudenabling/current/testfile.txt"
        tardis_url = "%s/api/v1/dataset_file/" % tardis_host_url
        #headers = {'content-type': 'application/json'}
        headers = {'Accept': 'application/json'}
        data = json.dumps({
            'dataset': str(header_location),
            'filename': 'testfile.txt',
            'size': 6,
            'mimetype': 'text/plain',
            'md5sum' : 'b1946ac92492d2347c6235b4d2611184'
            })

        logger.debug("data=%s" % data)
        r = requests.post(tardis_url, data={'json_data': data}, headers=headers,
                                files={'attached_file': open(filename, 'rb')},
                                auth=HTTPBasicAuth(tardis_user, tardis_pass)
                                )
        print r.json
        print r.text
        print r.headers



    def test_hrmc(self):

        if not settings.TEST_MYTARDIS_IP:
            raise SkipTest

        file_info = (
            'test/sweep01/run02/output_1/node01',
            'test/sweep01/run02/output_1/node02',
            'test/sweep01/run02/output_2/node01',
            'test/sweep01/run02/output_2/node02',
            'test/sweep01/run02/output_3/node01',
            'test/sweep01/run02/output_3/node02',
            )

        exp_id = 0
        for file_path in file_info:

            source_url = smartconnector.get_url_with_pkey(
                self.settings, file_path,
                is_relative_path=True)
            logger.debug("source_url=%s"  % source_url)
            exp_id = mytardis.post_dataset(settings=self.settings,
                source_url=source_url,
                exp_id=exp_id,
                dataset_schema="http://rmit.edu.au/schemas/hrmcdataset/output")











