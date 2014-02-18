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
import json
import logging
from pprint import pformat
from bdphpcprovider.platform import manage
from bdphpcprovider.corestages import Transform

from bdphpcprovider.corestages.stage import Stage, UI
from bdphpcprovider.smartconnectorscheduler import models

from bdphpcprovider import mytardis
from bdphpcprovider import messages
from bdphpcprovider import storage

from bdphpcprovider.runsettings import getval, getvals, setval, update, SettingNotFoundException
from bdphpcprovider.storage import get_url_with_pkey



logger = logging.getLogger(__name__)


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class Rand2Transform(Transform):
    def curate_dataset(self, run_settings, experiment_id, base_dir, output_url,
        all_settings):

        OUTCAR_FILE = "OUTCAR"
        VALUES_FILE = "output"
        logger.debug('output_url=%s' % output_url)
        iteration = int(getval(run_settings, '%s/system/id' % RMIT_SCHEMA))
        iter_output_dir = os.path.join(os.path.join(base_dir, "output_%s" % iteration))
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)
        logger.debug('iter_output_dir=%s' % iter_output_dir)
        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        fsys = storage.get_filesystem(output_url)
        node_output_dirnames, _ = fsys.listdir(mypath)
        logger.debug('node_output_dirnames=%s' % node_output_dirnames)

        for i, node_output_dirname in enumerate(node_output_dirnames):
            node_path = os.path.join(iter_output_dir, node_output_dirname)
            logger.debug("output_url=%s" % output_url)

            values_url = storage.get_url_with_pkey(all_settings,
                os.path.join(node_path, VALUES_FILE), is_relative_path=False)
            logger.debug("values_url=%s" % values_url)
            try:
                values_content = storage.get_file(values_url)
                val1 = values_content.split()[0]
                val2 = values_content.split()[1]
                logger.debug('val1=%s, val2=%s' % (val1, val2))
            except IOError, e:
                logger.error(e)

            # FIXME: all values from map are strings initially, so need to know
            # type to coerce.
            x = val1
            try:
                x = float(val1)
            except IndexError:
                pass
            except ValueError:
                pass

            logger.debug("x=%s" % x)

            y = val2

            try:
                y = float(val2)
            except IndexError:
                pass
            except ValueError:
                pass
            logger.debug("y=%s" % y)

            def _get_exp_name_for_vasp(settings, url, path):
                """
                Break path based on EXP_DATASET_NAME_SPLIT
                """
                return str(path)

            def _get_dataset_name_for_vasp(settings, url, path):
                """
                Break path based on EXP_DATASET_NAME_SPLIT
                """
                return all_settings['graph_point_id']
                #return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            source_dir_url = get_url_with_pkey(
                    all_settings,
                    node_path,
                    is_relative_path=False)

            all_settings['graph_point_id'] = str(i)
            experiment_id = mytardis.create_dataset(
                settings=all_settings,
                source_url=source_dir_url,
                exp_id=experiment_id,
                exp_name=_get_exp_name_for_vasp,
                dataset_name=_get_dataset_name_for_vasp,
                dataset_paramset=[
                    mytardis.create_paramset("remotemake/output", []),
                    mytardis.create_graph_paramset("dsetgraph",
                        name="randdset",
                        graph_info={},
                        value_dict={"randdset/x": x, "randdset/y": y}
                            if (x is not None)
                                and (y is not None)
                                else {},
                        value_keys=[]
                        ),
                    ]
                )

        return experiment_id






