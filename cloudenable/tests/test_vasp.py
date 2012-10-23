import unittest
import os
import logging
import logging.config
from smartconnector import Stage
from stages.vasp import VASP
from filesystem import DataObject
from filesystem import FileSystem

from stages.vasp import process_all


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

    # def test_vasp_extraction(self):
    #     """ Extract metadata from a set of VASP datafiles into a JSON file"""
    #     path = os.path.abspath(os.path.join(".","testing","dataset1"))
    #     res = process_all(path)
    #     import json
    #     dump = json.dumps(res, indent=1)
    #     # read in stored correct answer
    #     test_text = open(os.path.join(path, 'test_check.json'), 'r').read()
    #     print dump
    #     self.assertEquals(dump, test_text)

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





