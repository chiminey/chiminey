import unittest
import os

from smartconnector import Stage
from stages.vasp import VASP

from stages.vasp import process_all





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

    def test_vasp_extraction(self):
        """ Extract metadata from a set of VASP datafiles into a JSON file"""
        path = os.path.abspath(os.path.join(".","testing","dataset1"))
        res = process_all(path)
        import json
        dump = json.dumps(res, indent=1)
        # read in stored correct answer
        test_text = open(os.path.join(path, 'test_check.json'), 'r').read()
        print dump
        self.assertEquals(dump, test_text)

    def test_stage(self):

        s1 = VASP()
        context = {}

        fs = FileSystem(self.global_filesystem, self.local_filesystem)

        files_to_copy = fs.get_local_subdirectory_files(self.output_dir,
                                             node_dir)

        # move input files to fs
        from shutil import copytree
        copytree(os.path.join("..","testing","dataset1"),
                 os.path.join(self.global_filesystem,"vasp"))

        res = s1.triggered(context)
        self.assertEquals(res, True)

        s1.process(context)

        context = s1.output(context)


        import json
        dump = json.dumps(res, indent=1)


        test_text = open(os.path.join(path, 'test_check.json'), 'r').read()






