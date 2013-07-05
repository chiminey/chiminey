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

from django.contrib.auth.models import User
from django import test as djangotest
from bdphpcprovider.smartconnectorscheduler.management.commands import view
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector

from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException
logger = logging.getLogger(__name__)

def error(e):
    raise


class TestBDPURLS(unittest.TestCase):
    """
    Test functions that manipulate BDPURLS
    """

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def test_get_url_with_key(self):

        models.Platform.objects.get_or_create(name='nci',
            root_path="/var/cloudenabling/nci")
        models.Platform.objects.get_or_create(name='local',
            root_path="/var/cloudenabling/remotesys")


        settings = {
            'nci_private_key':'nci_private_key',
            'nci_user': 'nci_user',
            'nci_password': 'nci_password'
        }
        url = "ssh://nci@127.0.0.1/remote/greet.txt"

        res = smartconnector.get_url_with_pkey(settings, url)

        self.assertEquals("ssh://127.0.0.1/remote/greet.txt?"
            "key_file=nci_private_key&password=nci_password&"
            "root_path=/var/cloudenabling/nci&username=nci_user", res)

        url = "ssh://127.0.0.1/foo/bar.txt"

        res = smartconnector.get_url_with_pkey(settings, url)

        self.assertEquals("file://127.0.0.1/foo/bar.txt?"
            "root_path=/var/cloudenabling/remotesys", res)


        url = 'file://local@127.0.0.1/local/finalresult.txt'

        res = smartconnector.get_url_with_pkey(settings, url)

        self.assertEquals("file://127.0.0.1/local/finalresult.txt?"
            "root_path=/var/cloudenabling/remotesys", res)

        url = 'file://local@127.0.0.1/local/finalresult.txt'

        res = smartconnector.get_url_with_pkey(settings, url)

        self.assertEquals("file://127.0.0.1/local/finalresult.txt?root_path=/var/cloudenabling/remotesys", res)

        url = 'file://127.0.0.1/hrmcrun/input_0'

        res = smartconnector.get_url_with_pkey(settings, url)

        self.assertEquals("file://127.0.0.1/hrmcrun/input_0?root_path=/var/cloudenabling/remotesys", res)

        url = 'celery_payload_2'

        res = smartconnector.get_url_with_pkey(settings, url, is_relative_path=True)

        self.assertEquals("file://127.0.0.1/celery_payload_2/?root_path=/var/cloudenabling/remotesys", res)

        url = 'nci@celery_payload_2'

        res = smartconnector.get_url_with_pkey(settings, url, is_relative_path=True)

        self.assertEquals("ssh://127.0.0.1/celery_payload_2/?key_file=nci_private_key&password=nci_password&root_path=/var/cloudenabling/nci&username=nci_user", res)


class TestCopy(unittest.TestCase):

    def setUp(self):
        models.Platform.objects.get_or_create(name='local',
            root_path="/var/cloudenabling/remotesys")

    def tearDown(self):
        pass

    def test_copydir_rel(self):

        self.settings = {'mytardis_user': 'mytardis',
            'mytardis_password': 'dtofaamdtofaam',
            'mytardis_host': '115.146.85.142'}

        file_info = (
            ('user/testdir/file1.txt', "content1"),
            ('user/testdir/dir/file2.txt', "content2")
        )

        final_file_info = {
            'user/testdir2/file1.txt': 'content1',
            'user/testdir2/dir/file2.txt': 'content2'
        }
        final_file_info = {
                'user/testdir2/file1.txt': 'content1',
                'user/testdir2/dir/file2.txt': 'content2'
            }


        for fpath, content in file_info:
            dest_url = smartconnector.get_url_with_pkey(self.settings,
                fpath, is_relative_path=True)
            hrmcstages.put_file(dest_url, content.encode('utf-8'))
        source_url = smartconnector.get_url_with_pkey(self.settings,
            'user/testdir', is_relative_path=True)
        destination_url = smartconnector.get_url_with_pkey(self.settings,
            'user/testdir2', is_relative_path=True)
        hrmcstages.copy_directories(source_url, destination_url)

        files_list = hrmcstages.list_all_files(destination_url)
        self.assertEquals(len(files_list), len(file_info))
        for path in files_list:
            logger.debug(path)
            relpath = smartconnector.get_url_with_pkey(self.settings,
                path, is_relative_path=True)
            content = hrmcstages.get_file(relpath)
            logger.debug(content)
            self.assertEquals(final_file_info[path], content)

        hrmcstages.delete_files(destination_url, [])
        hrmcstages.delete_files(source_url, [])


    def test_copydir_rel2(self):

        self.settings = {'mytardis_user': 'mytardis',
            'mytardis_password': 'dtofaamdtofaam',
            'mytardis_host': '115.146.85.142'}

        file_info = (
            ('testdir/file1.txt', "content1"),
            ('testdir/dir/file2.txt', "content2")
            )

        final_file_info = {
            'testdir2/file1.txt': 'content1',
            'testdir2/dir/file2.txt': 'content2'
            }

        for fpath, content in file_info:
            dest_url = smartconnector.get_url_with_pkey(self.settings,
                fpath, is_relative_path=True)
            hrmcstages.put_file(dest_url, content.encode('utf-8'))
        source_url = smartconnector.get_url_with_pkey(self.settings,
            'testdir', is_relative_path=True)
        destination_url = smartconnector.get_url_with_pkey(self.settings,
            'testdir2', is_relative_path=True)
        hrmcstages.copy_directories(source_url, destination_url)

        files_list = hrmcstages.list_all_files(destination_url)
        self.assertEquals(len(files_list), len(file_info))
        for path in files_list:
            logger.debug(path)
            relpath = smartconnector.get_url_with_pkey(self.settings,
                path, is_relative_path=True)
            content = hrmcstages.get_file(relpath)
            logger.debug(content)
            self.assertEquals(final_file_info[path], content)

        hrmcstages.delete_files(destination_url,[])
        hrmcstages.delete_files(source_url,[])



