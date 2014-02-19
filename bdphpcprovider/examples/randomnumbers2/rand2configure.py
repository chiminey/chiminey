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
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages import Configure
from bdphpcprovider import mytardis
from bdphpcprovider.runsettings import getval

logger = logging.getLogger(__name__)
SCHEMA_PREFIX = "http://rmit.edu.au/schemas"


class Rand2Configure(Configure):
    '''
        Sets up output locations and credentials, MyTardis credentials,
        and creates experiment in MyTardis
    '''
    def curate_data(self, run_settings, output_location, experiment_id):
        '''
           Creates experiment in MyTardis
        '''
        # Loading MyTardis credentials
        bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % SCHEMA_PREFIX)
        mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % SCHEMA_PREFIX)
        mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)

        def _get_experiment_name(path):
            '''
                Return the name for MyTardis experiment
                e.g., if path='x/y/z', returns 'y/z'
            '''
            return str(os.sep.join(path.split(os.sep)[-2:]))

        # Creates new experiment if experiment_id=0
        # If experiment_id is non-zero, the experiment is updated
        experiment_id = mytardis.create_experiment(
            settings=mytardis_settings, # MyTardis credentials
            exp_id=experiment_id,
            expname=_get_experiment_name(output_location), # name of the experiment in MyTardis
            # metadata associated with the experiment
            # a list of parameter sets
            experiment_paramset=[
                # a new blank parameter set conforming to schema 'remotemake'
                mytardis.create_paramset("remotemake", []),
                # a graph parameter set
                mytardis.create_graph_paramset("expgraph", # name of schema
                    name="randexp1", # unique graph name
                    graph_info={"axes":["x", "y"], "legends":["Random points"]}, # information about the graph
                    value_dict={}, # values to be used in parent graphs if appropriate
                    value_keys=[["randdset/x", "randdset/y"]]), # values from datasets to produce points in the graph
                           ])
        return experiment_id
