from django.test import TestCase
from django.test.client import Client
from django.conf import settings

from flexmock import flexmock
from tempfile import mkstemp
from string import lower

from bdphpcprovider.smartconnectorscheduler import views
from bdphpcprovider.smartconnectorscheduler import mc
from bdphpcprovider.smartconnectorscheduler import getresults

import os
import base64
import urllib2

class SmartConnectorSchedulerTest(TestCase):
    def setUp(self):
        self.index_url = '/index/'
        self.client = Client()
        self.experiment_id = '1'
        self.group_id = "TEST_ID000000"
        self.number_of_cores = '1'
        self.input_parameters = {'experiment_id' : self.experiment_id}
        self.input_parameters['group_id'] = self.group_id
        self.input_parameters['number_of_cores'] = self.number_of_cores

    # Testing Create Stage
    def test_index_create(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        print response.content

        current_stage = 'Create'
        self.input_parameters['stages'] = [current_stage]
        create_parameters= [lower(current_stage), '-v', self.number_of_cores]
        message = "Your group ID is %s" % self.group_id

        flexmock(mc).should_receive('start')\
        .with_args(create_parameters)\
        .and_return(self.group_id)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)


    # Testing Setup Stage
    def test_index_setup(self):
        current_stage = 'Setup'
        self.input_parameters['stages'] = [current_stage]
        setup_parameters= [lower(current_stage), '-g', self.group_id]
        message = "Setup stage completed"

        flexmock(mc).should_receive('start')\
        .with_args(setup_parameters)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)


    # Testing Run Stage
    def test_run(self):
        settings.BDP_INPUT_DIR_PATH = '/tmp/data/input'
        settings.BDP_OUTPUT_DIR_PATH = '/tmp/data/output'

        os.system('rm -rf %s' % settings.BDP_INPUT_DIR_PATH)
        os.system('mkdir -p %s' % settings.BDP_INPUT_DIR_PATH)

        temp_file = mkstemp()
        file_name = temp_file[1]
        input_file_basename = 'test_input.txt'
        input_file_name = '%s/%s' % (settings.BDP_INPUT_DIR_PATH,
                                     input_file_basename)
        os.system('mv %s %s ' % (file_name, input_file_name))
        file = open(input_file_name, "w")
        file.write("This is an input file...")
        file.close()
        zipped_file = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
        os.system("cd %s; zip %s %s" % (settings.BDP_INPUT_DIR_PATH,
                                        zipped_file, input_file_basename))
        file = open(zipped_file, "rb")
        b64_encoded = base64.b64encode(file.read())
        file.close()

        output_dir = '%s/%s/output' % (settings.BDP_OUTPUT_DIR_PATH,
                                       self.group_id)

        print 'output %s %s' % (output_dir, os.path.exists(output_dir))
        output_file = 'output.txt'
        command = 'rm -rf %s; mkdir -p %s; cd %s;'\
                  'mkdir output_1; cd output_1;'\
                  'echo "Computation completed" > %s'\
                  %(output_dir, output_dir, output_dir, output_file)
        os.system(command)

        zipped_input_dir = '%s/input.zip' % settings.BDP_INPUT_DIR_PATH
        extracted_input_dir = '%s/%s' % (settings.BDP_INPUT_DIR_PATH,
                                         self.group_id)
        unzip_inputdir_cmd =  'unzip -o -d %s %s' % (extracted_input_dir,
                                                     zipped_input_dir)

        flexmock(os).should_receive('system').with_args(unzip_inputdir_cmd)\
        .and_return(os.system(unzip_inputdir_cmd))

        rm_outputdir_cmd = 'rm -rf %s ' % output_dir
        flexmock(os).should_receive('system').with_args(rm_outputdir_cmd)

        fake_request = flexmock(request=lambda: 'requested')
        fake_response = flexmock(read=lambda: 'responded')
        flexmock(urllib2).should_receive('Request')\
        .and_return(fake_request)
        flexmock(urllib2).should_receive('urlopen')\
        .and_return(fake_response)
        flexmock(getresults).should_receive('get_results')\
        .with_args(self.experiment_id, self.group_id, output_dir)\
        .and_return(True)

        current_stage = 'Run'
        self.input_parameters['stages'] = [current_stage]
        self.input_parameters['input_dir'] = b64_encoded
        message = "Run stage completed. Results are ready"

        flexmock(mc).should_receive('start')\
        .and_return('COMPLETED')

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)


    # Testing Terminate Stage
    def test_index_terminate(self):
        current_stage = 'Terminate'
        self.input_parameters['stages'] = [current_stage]
        terminate_parameters=  ['teardown', '-g', self.group_id, 'yes']
        message = "Terminate stage completed"

        flexmock(mc).should_receive('start')\
        .with_args(terminate_parameters)

        flexmock(views).should_receive('callback')\
        .with_args(message, current_stage, self.group_id)

        response = self.client.post(self.index_url, data=self.input_parameters)
        self.assertEqual(response.status_code, 200)
