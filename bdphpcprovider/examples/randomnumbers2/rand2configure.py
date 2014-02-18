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
from pprint import pformat
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages import Configure

from bdphpcprovider.corestages.stage import Stage, UI
from bdphpcprovider.smartconnectorscheduler import models

from bdphpcprovider.corestages.sweep import post_mytardis_exp
from bdphpcprovider import mytardis
from bdphpcprovider import messages
from bdphpcprovider import storage

from bdphpcprovider.runsettings import getval, getvals, setval, update, SettingNotFoundException
from bdphpcprovider.storage import get_url_with_pkey



logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Rand2Configure(Configure):
    def curate_data(self, run_settings, output_location, experiment_id):
        #fixme: bring back ename
        experiment_id = post_mytardis_exp(
            run_settings=run_settings,
            experiment_id=experiment_id,
            output_location=output_location,
            experiment_paramset=[
                mytardis.create_paramset("remotemake", []),
                mytardis.create_graph_paramset("expgraph",
                    name="randexp1",
                    graph_info={"axes":["x", "y"], "legends":["Random points"]},
                    value_dict={},
                    value_keys=[["randdset/x", "randdset/y"]]),
                           ])
        return experiment_id
