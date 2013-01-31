# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the RMIT, the RMIT members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import unittest
import os
import logging
import logging.config
from bdphpcprovider.smartconnectorscheduler import Stage
from bdphpcprovider.smartconnectorscheduler.stages.vasp import VASP
from bdphpcprovider.smartconnectorscheduler.filesystem import DataObject, FileSystem


logger = logging.getLogger('tests')



class MetadataTests(unittest.TestCase):
    """
    Tests stage which extracts metadata from found VASP datafiles
    """

    keep_directories = True

    def setUp(self):

        import tempfile

        self.global_filesystem = tempfile.mkdtemp()
        logger.debug("global_filesystem=%s" % self.global_filesystem)
        self.local_filesystem = 'default'

        logging.config.fileConfig('logging.conf')
        self.vm_size = 100
        self.image_name = "ami-0000000d"  # FIXME: is hardcoded in
                                          # simplepackage
        self.instance_name = "foo"
        self.settings = {
            'USER_NAME':  "accountname", 'PASSWORD':  "mypassword",
            'GROUP_DIR_ID': "test", 'EC2_ACCESS_KEY': "",
            'EC2_SECRET_KEY': "", 'VM_SIZE': self.vm_size,
            'VM_IMAGE': "ami-0000000d",
            'PRIVATE_KEY_NAME': "", 'PRIVATE_KEY': "", 'SECURITY_GROUP': "",
            'CLOUD_SLEEP_INTERVAL': 0, 'GROUP_ID_DIR': "", 'DEPENDS': ('a',),
            'DEST_PATH_PREFIX': "package", 'PAYLOAD_CLOUD_DIRNAME': "package",
            'PAYLOAD_LOCAL_DIRNAME': "", 'COMPILER': "g77", 'PAYLOAD': "payload",
            'COMPILE_FILE': "foo", 'MAX_SEED_INT': 100, 'RETRY_ATTEMPTS': 3,
            'OUTPUT_FILES': ['a', 'b']}

    def test_stage(self):

        s1 = VASP()
        context = {}
        fs = FileSystem(self.global_filesystem, self.local_filesystem)
        input_path = os.path.join("testing", "dataset1")
        # move input files to fs
        from shutil import copytree
        copytree(os.path.abspath(input_path),
                 os.path.join(self.global_filesystem, "vasp"))
        print("fs=%s" % fs)
        context = {'filesys': fs}
        res = s1.triggered(context)
        self.assertEquals(res, True)
        s1.process(context)
        context = s1.output(context)
        import json
        config = fs.retrieve_new("output", "metadata.json")
        content = json.loads(config.retrieve())
        # dump = json.dumps(content, indent=1)
        # logger.debug("dump=%s" % dump)
        test_text = open(os.path.join(input_path, 'test_check.json'), 'r').read()
        test_dict = json.loads(test_text)
        logger.debug("test_text=%s" % test_text)
        self.assertEquals(content, test_dict)





