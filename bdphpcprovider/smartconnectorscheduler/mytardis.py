# Copyright (C) 2013, RMIT University

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
import hashlib
import re
import json
import requests
from requests.auth import HTTPBasicAuth


logger = logging.getLogger(__name__)

from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import hrmcstages

EXP_DATASET_NAME_SPLIT = 2


def _get_exp_name(settings, url, path):
    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))


def _get_dataset_name(settings, url, path):
    return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))


def post_dataset(settings,
        source_url,
        exp_id,
        exp_name=_get_exp_name,
        dataset_name=_get_dataset_name,
        dataset_schema=None):
    """
    POST to mytardis_host REST API with mytardis_user and mytardis_password credentials
    to create or update experiment for a new dataset containing datafiles from
    source_url BDP directory.  Experiment name is path up to last EXP_DATASET_NAME_SPLIT path elements
    and dataset is the rest of the path.
    FIXME: what if tardis in unavailable?
    """

    tardis_user = settings["mytardis_user"]
    tardis_pass = settings["mytardis_password"]
    tardis_host_url = "http://%s" % settings["mytardis_host"]
    logger.debug("posting dataset from %s to mytardis at %s" % (source_url, tardis_host_url))

    (source_scheme, source_location, source_path, source_location, query_settings) = hrmcstages.parse_bdpurl(source_url)

    logger.debug("source_path=%s" % source_path)
    if source_scheme == "file":
        root_path = hrmcstages.get_value('root_path', query_settings)
    else:
        raise InvalidInputError("only file source_schema supported for source of mytardis transfer")

    # get existing experiment or create new
    new_exp_id = exp_id

    exp_id_pat = re.compile(".*/([0-9]+)/$")
    if not new_exp_id:
        logger.debug("creating new experiment")

        url = "%s/api/v1/experiment/?format=json" % tardis_host_url
        headers = {'content-type': 'application/json'}
        data = json.dumps({
            'title': exp_name(settings, source_url, source_path),
            'description': 'some test repo'})
        logger.debug("data=%s" % data)
        r = requests.post(url,
            data=data,
            headers=headers,
            auth=(tardis_user, tardis_pass))

        # FIXME: need to check for status_code and handle failures.

        logger.debug(r.json)
        logger.debug(r.text)
        logger.debug(r.headers)

        new_experiment_location = r.headers['location']
        logger.debug("new_experiment_location=%s" % new_experiment_location)
        exp_id_mat = exp_id_pat.match(new_experiment_location)
        if exp_id_mat:
            exp_id_str = exp_id_mat.group(1)
            try:
                new_exp_id = int(exp_id_str)
            except ValueError:
                logger.error("cannot create mytardis experiment")
                new_exp_id = 0
                # cannot create experiment, but could try next time
            logger.debug("new_exp_id=%s" % new_exp_id)
        else:
            logger.warn("could not match experiment_id pattern")
    else:
        logger.debug("using existing experiment at %s" % new_exp_id)

    new_experiment_uri = "/api/v1/experiment/%s/" % new_exp_id

    # save dataset
    logger.debug("saving dataset in experiment at %s" % new_exp_id)
    url = "%s/api/v1/dataset/?format=json" % tardis_host_url
    headers = {'content-type': 'application/json'}
    # FIXME: the split of source_path into experiment/dataset name sections
    # needs to be generalised

    schemas = [{
                "schema": "http://rmit.edu.au/schemas/hrmcdataset",
                "parameters": []
               }]
    if dataset_schema:
        schemas.append({
            "schema": dataset_schema,
            "parameters": []
            })
    logger.debug("schemas=%s" % schemas)
    data = json.dumps({
        'experiments': [new_experiment_uri],
        'description': dataset_name(settings, source_url, source_path),
        "parameter_sets": schemas
            })
    logger.debug("data=%s" % data)
    r = requests.post(url, data=data, headers=headers, auth=HTTPBasicAuth(tardis_user, tardis_pass))
    logger.debug("r.json=%s" % r.json)
    logger.debug("r.text=%s" % r.text)
    logger.debug("r.headers=%s" % r.headers)
    header_location = r.headers['location']
    new_dataset_uri = header_location[len(tardis_host_url):]

    # move files across
    source_files = hrmcstages.list_all_files(source_url)
    logger.debug("source_files=%s" % source_files)
    url = "%s/api/v1/dataset_file/" % tardis_host_url
    headers = {'Accept': 'application/json'}

    for file_location in source_files:

        file_path = os.path.join(root_path, file_location)
        logger.debug("file_path=%s" % file_path)
        #logger.debug("content=%s" % open(file_path,'rb').read())
        data = json.dumps({
            'dataset': str(new_dataset_uri),
            'filename': os.path.basename(file_path),
            'size': os.stat(file_path).st_size,
            'mimetype': 'text/plain',
            'md5sum': hashlib.md5(open(file_path, 'r').read()).hexdigest()
            })
        logger.debug("data=%s" % data)

        r = requests.post(url, data={'json_data': data}, headers=headers,
            files={'attached_file': open(file_path, 'rb')},
            auth=HTTPBasicAuth(tardis_user, tardis_pass)
            )

        logger.debug("r.js=%s" % r.json)
        logger.debug("r.te=%s" % r.text)
        logger.debug("r.he=%s" % r.headers)

    return new_exp_id
