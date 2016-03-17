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

import logging
import os
import json
from chiminey.corestages import Execute
from chiminey.runsettings import update
from chiminey.storage import get_url_with_credentials, get_file
from chiminey.mytardis import create_dataset, create_paramset


logger = logging.getLogger(__name__)


class HRMCExecute(Execute):

    def set_domain_settings(self, run_settings, local_settings):
        update(local_settings, run_settings,
               '%s/input/hrmc/iseed' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/optimisation_scheme' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/pottype' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/fanout_per_kept_result' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/optimisation_scheme' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/threshold' % self.SCHEMA_PREFIX,
               '%s/input/hrmc/pottype' % self.SCHEMA_PREFIX,
               '%s/system/max_seed_int' % self.SCHEMA_PREFIX,)

    def curate_data(self, experiment_id, local_settings, output_storage_settings,
                    mytardis_settings, source_files_url):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        output_host = output_storage_settings['host']

        EXP_DATASET_NAME_SPLIT = 2

        def _get_exp_name_for_input(settings, url, path):
            return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

        def _get_dataset_name_for_input(settings, url, path):
            logger.debug("path=%s" % path)
            source_url = get_url_with_credentials(
                output_storage_settings,
                output_prefix + os.path.join(output_host, path, self.VALUES_FNAME),
                is_relative_path=False)
            logger.debug("source_url=%s" % source_url)
            try:
                content = get_file(source_url)
            except IOError:
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            logger.debug("content=%s" % content)
            try:
                values_map = dict(json.loads(str(content)))
            except Exception, e:
                logger.warn("cannot load %s: %s" % (content, e))
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            try:
                iteration = str(path.split(os.sep)[-2:-1][0])
            except Exception, e:
                logger.error(e)
                iteration = ""

            if "_" in iteration:
                iteration = iteration.split("_")[1]
            else:
                iteration = "initial"

            if 'run_counter' in values_map:
                run_counter = values_map['run_counter']
            else:
                run_counter = 0

            dataset_name = "%s_%s" % (iteration,
                                      run_counter)
            logger.debug("dataset_name=%s" % dataset_name)
            return dataset_name

        local_settings.update(mytardis_settings)
        experiment_id = create_dataset(
            settings=local_settings,
            source_url=source_files_url,
            exp_id=experiment_id,
            exp_name=_get_exp_name_for_input,
            dataset_name=_get_dataset_name_for_input,
            experiment_paramset=[],
            dataset_paramset=[
                create_paramset('hrmcdataset/input', [])])
        return experiment_id
