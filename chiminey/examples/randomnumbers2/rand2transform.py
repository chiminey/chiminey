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


import os
import logging
from chiminey.corestages import Transform
from chiminey import mytardis
from chiminey import storage
from chiminey.runsettings import getval
from chiminey.storage import get_url_with_credentials

logger = logging.getLogger(__name__)
SCHEMA_PREFIX = "http://rmit.edu.au/schemas"
OUTPUT_FILE = "output"


class Rand2Transform(Transform):
    '''
        Curates dataset into existing MyTardis experiment
    '''
    def curate_dataset(self, run_settings, experiment_id,
                       base_url, output_url, all_settings):
        '''
            Curates dataset
        '''
        # Retrieves process directories below the current output location
        iteration = int(getval(run_settings, '%s/system/id' % SCHEMA_PREFIX))
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        current_output_url = "%s%s" % (output_prefix, os.path.join(os.path.join(
            base_url, "output_%s" % iteration)))
        (scheme, host, current_output_path, location, query_settings) = storage.parse_bdpurl(output_url)
        output_fsys = storage.get_filesystem(output_url)
        process_output_dirs, _ = output_fsys.listdir(current_output_path)

        # Curates a dataset with metadata per process
        for i, process_output_dir in enumerate(process_output_dirs):
            # Expand the process output directory and add credentials for access
            process_output_url = '/'.join([current_output_url, process_output_dir])
            process_output_url_with_cred = get_url_with_credentials(
                    all_settings,
                    process_output_url,
                    is_relative_path=False)
            # Expand the process output file and add credentials for access
            output_file_url_with_cred = storage.get_url_with_credentials(
                all_settings, '/'.join([process_output_url, OUTPUT_FILE]),
                is_relative_path=False)
            try:
                output_content = storage.get_file(output_file_url_with_cred)
                val1, val2 = output_content.split()
            except (IndexError, IOError) as e:
                logger.warn(e)
                continue
            try:
                x = float(val1)
                y = float(val2)
            except (ValueError, IndexError) as e:
                logger.warn(e)
                continue

            # Returns the process id as MyTardis dataset name
            all_settings['graph_point_id'] = str(i)
            def _get_dataset_name(settings, url, path):
                return all_settings['graph_point_id']

            # Creates new dataset and adds to experiment
            # If experiment_id==0, creates new experiment
            experiment_id = mytardis.create_dataset(
                settings=all_settings, # MyTardis credentials
                source_url=process_output_url_with_cred,
                exp_id=experiment_id,
                dataset_name=_get_dataset_name, # the function that defines dataset name
                dataset_paramset=[
                    # a new blank parameter set conforming to schema 'remotemake/output'
                    mytardis.create_paramset("remotemake/output", []),
                    mytardis.create_graph_paramset("dsetgraph", # name of schema
                        name="randdset", # a unique dataset name
                        graph_info={},
                        value_dict={"randdset/x": x, "randdset/y": y},  # values to be used in experiment graphs
                        value_keys=[]
                        ),
                    ]
                )
        return experiment_id






