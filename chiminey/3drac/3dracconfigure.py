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

import ast
import os
import logging
from pprint import pformat
from chiminey.platform import manage
from chiminey.corestages import stage
from chiminey.platform import *

from chiminey.corestages.stage import Stage, UI
from chiminey.smartconnectorscheduler import models

from chiminey import mytardis
from chiminey import messages
from chiminey import storage

from chiminey.corestages.configure import Configure
from chiminey.smartconnectorscheduler.errors import InvalidInputError
from chiminey.runsettings import getval, getvals, setval, setvals, update, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, file_exists, get_file, get_filep
from django.core.exceptions import ImproperlyConfigured
from chiminey.smartconnectorscheduler import jobs

from chiminey.storage import get_url_with_credentials, list_dirs, get_make_path

logger = logging.getLogger(__name__)


from django.conf import settings as django_settings


class RAC3DConfigure(Configure):
    """
        - Setups up remote file system
           e.g. Object store in NeCTAR Creates file system,
    """

    def get_valid_coord_list(self,dfname,coordlist):
        row_count = 0
        column_count = 0
        data_valid = True
        prev_column_count = 0
        valid_coord_list =[]
        invalid_coord_list =""

        file_content = get_file(dfname)
        #logger.debug("content=%s" % file_content) 
        #with get_filep(dfname) as fp:
            #for line in fp:
            #logger.debug("line=%s" % line) 

        for line in file_content.split("\n"):
            if len(line) != 0:
                row_count += 1
                row_content = line.split()
                column_count = len(row_content) - 1
                if prev_column_count == 0:
                    prev_column_count = column_count
                if column_count == prev_column_count:
                     data_valid = True
                else:
                     data_valid = False
 
        if row_count == column_count:
            data_valid = True
        else:
            data_valid = False
    
        if data_valid == False:
            message = 'Invalid data file  - row items count: %d does not match column count: %d ' %(row_count, column_count)
            logger.error(message)
            raise InvalidInputError(message)
    
        for coord in coordlist: 
            logger.debug("Coord = %s, coord_length = %d, line_length = %d, line_count = %d" % (str(coord), len(coord),row_count,column_count))
            if len(coord) != 3:
                invalid_coord_list = invalid_coord_list + str(coord) + ' : each block description list need to have three papameters \n'
            elif coord[0] < 0 or coord[1] < 0 or coord[2] < 0:
                invalid_coord_list = invalid_coord_list + str(coord) + ' : a block description list can not have negetive value \n'
            elif coord[0] + coord[2] > column_count or coord[1] + coord[2] > row_count :
                invalid_coord_list = invalid_coord_list + str(coord) + ' : bock size %d exceeds file boundary \n' %(coord[2])
            else:
                valid_coord_list.append(coord)
        return (valid_coord_list, invalid_coord_list)
  

    def copy_to_scratch_space(self, run_settings, local_settings, result_offset):
        bdp_username = run_settings['%s/bdp_userprofile' % django_settings.SCHEMA_PREFIX]['username']
        output_storage_url = run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['platform_url']
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)

        run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset'] = self.output_loc_offset
        offset = run_settings['%s/platform/storage/output' % django_settings.SCHEMA_PREFIX]['offset']
        self.job_dir = manage.get_job_dir(output_storage_settings, offset)
        iter_inputdir = os.path.join(self.job_dir, result_offset)
        logger.debug("iter_inputdir=%s" % iter_inputdir)

        input_storage_settings = self.get_platform_settings(run_settings, '%s/platform/storage/input' % django_settings.SCHEMA_PREFIX)
        #input_location = run_settings[django_settings.SCHEMA_PREFIX + '/input/system']['input_location']

        try:
            input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/system/input_location')
        except SettingNotFoundException:
            try:
		input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input_location')
	    except:
		input_location = getval(run_settings, django_settings.SCHEMA_PREFIX + '/input/location/input/input_location')
        logger.debug("input_location=%s" % input_location)
        #todo: input location will evenatually be replaced by the scratch space that was used by the sweep
        #todo: the sweep will indicate the location of the scratch space in the run_settings
        #todo: add scheme (ssh) to inputlocation

        #source_url = get_url_with_credentials(local_settings, input_location)

        input_offset = run_settings['%s/platform/storage/input' % django_settings.SCHEMA_PREFIX]['offset']
        input_url = "%s://%s@%s/%s" % (input_storage_settings['scheme'],
                                       input_storage_settings['type'],
                                       input_storage_settings['host'], input_offset)
        source_url = get_url_with_credentials(
            input_storage_settings, input_url, is_relative_path=False)

        logger.debug("source_url=%s" % source_url)

        destination_url = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                             output_storage_settings['type'],
                             iter_inputdir),
            is_relative_path=False)
        logger.debug("destination_url=%s" % destination_url)
        #storage.copy_directories(source_url, destination_url)

        if '%s/input/3drac' % django_settings.SCHEMA_PREFIX in run_settings:
            try:
                self.data_file = getval(run_settings, '%s/input/3drac/data_file_name' % django_settings.SCHEMA_PREFIX)
                logger.debug('Data file name =%s' % self.data_file)
            except ValueError:
                logger.error("cannot convert %s to data file name" % getval(run_settings, '%s/input/3drac/data_file_name' % django_settings.SCHEMA_PREFIX))

            try: 
                virtual_blocks = getval(run_settings, '%s/input/3drac/virtual_blocks_list' % django_settings.SCHEMA_PREFIX)
                self.vb_list = ast.literal_eval(virtual_blocks)
                logger.debug('Virtual blocks list =%s' % str(self.vb_list))
            except ValueError:
                logger.error("cannot convert %s to virtual block list %s" % getval(run_settings, '%s/input/3drac/virtual_blocks_list' % django_settings.SCHEMA_PREFIX))

        datafile_location = "%s://%s@%s/%s/initial/%s" % (input_storage_settings['scheme'],
                                       input_storage_settings['type'],
                                       input_storage_settings['host'], input_offset,self.data_file)
        datafile_url = get_url_with_credentials(
            input_storage_settings, datafile_location, is_relative_path=False)
        logger.debug("datafile_url=%s" % datafile_url)
        
        (valid_virtual_blocks_list, invalid_virtual_blocks_list) = self.get_valid_coord_list(datafile_url,self.vb_list)
        self.vb_list = valid_virtual_blocks_list
        logger.debug("valid_virtual_blocks_list=%s" % str(valid_virtual_blocks_list))
        logger.debug("self.vb_list=%s" % str(self.vb_list))
     

        invalid_blocks_list_location = "%s://%s@%s/%s/initial/%s" % (input_storage_settings['scheme'],
                                       input_storage_settings['type'],
                                       input_storage_settings['host'], input_offset,'invalid_blocks_list.txt')
        invalid_blocks_list_url = get_url_with_credentials(
            input_storage_settings, invalid_blocks_list_location, is_relative_path=False)
        logger.debug("invalid_blocks_list_url=%s" % invalid_blocks_list_url)

        #create 'invalid_blocks_list.txt' in 'source_url' location
        storage.put_file(invalid_blocks_list_url, invalid_virtual_blocks_list)
        logger.debug("invalid_virtual_blocks_list=%s" % invalid_virtual_blocks_list)

        #copy all files from 'source_url' to 'destination_url' location
        storage.copy_directories(source_url, destination_url)


    def output(self, run_settings):
        self.writeout_output(run_settings)
        self.writeout_input(run_settings)
        self.writeout_computation(run_settings)
        setval(run_settings,
               '%s/stages/configure/configure_done' % django_settings.SCHEMA_PREFIX,
               1)
        setval(run_settings,
               '%s/input/mytardis/experiment_id' % django_settings.SCHEMA_PREFIX,
               str(self.experiment_id))

        #change the value of virtual_blocks_list in run_settings
        setval(run_settings,
               '%s/input/3drac/virtual_blocks_list' % django_settings.SCHEMA_PREFIX,
               str(self.vb_list))
        logger.debug('run_settings=%s' % run_settings)
        return run_settings
