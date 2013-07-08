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
    """
    Break path based on EXP_DATASET_NAME_SPLIT
    """
    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))


def _get_dataset_name(settings, url, path):
    """
    Break path based on EXP_DATASET_NAME_SPLIT
    """
    return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))


# def post_exp_parameterset(settings,
#     exp_id,
#     experiment_schema):

#     tardis_user = settings["mytardis_user"]
#     tardis_pass = settings["mytardis_password"]
#     tardis_host_url = "http://%s" % settings["mytardis_host"]
#     logger.debug("posting exp metadata to mytardis at %s" % tardis_host_url)

#     url = "%s/api/v1/experiment/?format=json" % tardis_host_url
#     headers = {'content-type': 'application/json'}
#     schemas = [{
#                 "schema": "http://rmit.edu.au/schemas/hrmcexp",
#                 "parameters": []
#                }]
#     data = json.dumps({
#         'title': exp_name(settings, source_url, source_path),
#         'description': 'some test repo',
#         "parameter_sets": schemas})
#     logger.debug("data=%s" % data)
#     r = requests.post(url,
#         data=data,
#         headers=headers,
#         auth=(tardis_user, tardis_pass))

#     # TODO: need to check for status_code and handle failures by repolling.

#     logger.debug(r.json)
#     logger.debug(r.text)
#     logger.debug(r.headers)

def post_dataset(settings,
        source_url,
        exp_id,
        exp_name=_get_exp_name,
        dataset_name=_get_dataset_name,
        dataset_schema=None):
    """
    POST to mytardis_host REST API with mytardis_user and mytardis_password
    credentials to create or update experiment for a new dataset containing
    datafiles from source_url BDP directory.

    exp_name and dataset_name are supplied functions that break up the
    experiment and dataset names respectively.

    dataset_schema is the namespace of the schema at the mytardis that will
    be tagged to the dataset.

    FIXME: What if tardis in unavailable?  Connection to mytardis probably
    better handled as sperate celery subtask, which can retry until working and
    be async

    FIXME: this method is not generic enough to handle all situations. e.g.,
    it sets hrmc* schemas which should be parameters like dataset_schema

    FIXME: missing all error checking and retrying of connection to mytardis.
    """

    tardis_user = settings["mytardis_user"]
    tardis_pass = settings["mytardis_password"]
    tardis_host_url = "http://%s" % settings["mytardis_host"]
    logger.debug("posting dataset from %s to mytardis at %s" % (source_url,
        tardis_host_url))

    (source_scheme, source_location, source_path, source_location,
        query_settings) = hrmcstages.parse_bdpurl(source_url)

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
        schemas = [{
                    "schema": "http://rmit.edu.au/schemas/hrmcexp",
                    "parameters": []
                   }]
        data = json.dumps({
            'title': exp_name(settings, source_url, source_path),
            'description': 'some test repo',
            "parameter_sets": schemas})
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

    # FIXME: schema should be a parameter
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
    # FIXME: need to check for status_code and handle failures.

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
        # FIXME: need to check for status_code and handle failures.

        logger.debug("r.js=%s" % r.json)
        logger.debug("r.te=%s" % r.text)
        logger.debug("r.he=%s" % r.headers)

    return new_exp_id


def _extract_id_from_location(name, r):
    if 'location' in r.headers:
        id_pat = re.compile(".*/([0-9]+)/$")
        new_location = r.headers['location']

        logger.debug("new_location=%s" % new_location)
        id_mat = id_pat.match(new_location)
        if id_mat:
            id_str = id_mat.group(1)
            try:
                new_id = int(id_str)
            except ValueError:
                logger.error("cannot create mytardis new_id")
                new_id = 0
                # cannot create experiment, but could try next time
            logger.debug("new_id=%s" % new_id)
        else:
            logger.warn("could not match id pattern")
        return new_id
    else:
        logger.error("problem creating %s" % name)
        return 0


def get_or_create_experiment(query_settings, exp_name):

    headers = {'content-type': 'application/json'}
    tardis_user = query_settings["mytardis_username"]
    tardis_pass = query_settings["mytardis_password"]
    tardis_host_url = "http://%s" % query_settings["mytardis_host"]
    tardis_url = "%s/api/v1/experiment/?limit=0&format=json" % tardis_host_url
    r = requests.get(tardis_url, headers=headers, auth=(tardis_user, tardis_pass))
    logger.debug(r.json)
    logger.debug(r.text)
    logger.debug(r.headers)
    # TODO: better done in server side using api search filter
    try:
        ids = [(x['id'], x['title']) for x in r.json()['objects'] if x['title'] == exp_name]
    except TypeError:
        logger.error("r.json()=%s" % r.json())
        raise
    if ids:
        return (ids[0][0], False)
    else:

        url = "%s/api/v1/experiment/?format=json" % tardis_host_url
        headers = {'content-type': 'application/json'}
        schemas = [{
                    "schema": "http://rmit.edu.au/schemas/hrmcexp",
                    "parameters": []
                   }]
        data = json.dumps({
            'title': exp_name,
            'description': 'some test repo',
            "parameter_sets": schemas})
        logger.debug("data=%s" % data)
        r = requests.post(url,
            data=data,
            headers=headers,
            auth=(tardis_user, tardis_pass))

        logger.debug(r.json)
        logger.debug(r.text)
        logger.debug(r.headers)
        new_exp_id = _extract_id_from_location(exp_name, r)
        return (new_exp_id, True)


def _get_dataset(settings, dataset_name, exp_id):
    headers = {'content-type': 'application/json'}
    tardis_user = settings["mytardis_username"]
    tardis_pass = settings["mytardis_password"]
    tardis_host_url = "http://%s" % settings["mytardis_host"]
    tardis_url = "%s/api/v1/dataset/?limit=0&format=json" % tardis_host_url
    r = requests.get(tardis_url, headers=headers, auth=(tardis_user, tardis_pass))

    experiment_uri = "/api/v1/experiment/%s/" % exp_id
    #logger.debug("r.json()=%s" % r.json())
    # TODO: better done in server side using api search filter
    r_json = r.json()
    if 'objects' not in r_json:
        logger.error("no objects field in mytardis dataset GET command")
        return []
    ids = [x['id'] for x in r.json()['objects'] if experiment_uri in x['experiments'] and x['description'] == dataset_name]
    return ids


def get_or_create_dataset(settings, dataset_name, exp_id, dataset_schema=None):
    ids = _get_dataset(settings, dataset_name, exp_id)

    if not ids:
        tardis_host_url = "http://%s" % settings["mytardis_host"]
        tardis_user = settings["mytardis_username"]
        tardis_pass = settings["mytardis_password"]
        headers = {'content-type': 'application/json'}
        # FIXME: schema should be a parameter
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
            'experiments': ["/api/v1/experiment/%s/" % exp_id],
            'description': dataset_name,
            "parameter_sets": schemas
                })
        logger.debug("data=%s" % data)
        r = requests.post("%s/api/v1/dataset/?format=json" % tardis_host_url,
            data=data,
            headers=headers,
            auth=HTTPBasicAuth(tardis_user, tardis_pass))
        # FIXME: need to check for status_code and handle failures.

        logger.debug("r.json=%s" % r.json)
        logger.debug("r.text=%s" % r.text)
        logger.debug("r.headers=%s" % r.headers)

        return (_extract_id_from_location(dataset_name, r), True)

    else:
        return (ids[0], False)


def get_datafile(
        dest_url,
        ):
    """
       Do post to mytardis to create new datafile and any exp and dataset if
       needed
    """
    (source_scheme, tardis_host_url, source_path, source_location,
        query_settings) = hrmcstages.parse_bdpurl(dest_url)

    query_settings['mytardis_host'] = tardis_host_url

    logger.debug("query_settings=%s" % query_settings)

    exp_name = hrmcstages.get_value('exp_name', query_settings)
    dataset_name = hrmcstages.get_value('dataset_name', query_settings)
    root_path = hrmcstages.get_value('root_path', query_settings)
    fname = hrmcstages.get_value('fname', query_settings)
    tardis_user = hrmcstages.get_value('mytardis_username', query_settings)
    tardis_pass = hrmcstages.get_value('mytardis_password', query_settings)

    exp_id, _ = get_or_create_experiment(query_settings, exp_name)
    dataset_id, _ = get_or_create_dataset(query_settings, dataset_name, exp_id)

    url = "http://%s/api/v1/dataset_file/%s/" % (tardis_host_url, dataset_id)
    headers = {'Accept': 'application/json'}

    logger.debug("fname=%s" % fname)
    file_path = os.path.join(root_path, fname)
    logger.debug("file_path=%s" % file_path)
    #logger.debug("content=%s" % open(file_path,'rb').read())
    # data = json.dumps({
    #     'dataset': str(new_dataset_uri),
    #     'filename': os.path.basename(fname),
    #     'size': os.stat(temp.name).st_size,
    #     'mimetype': 'text/plain',
    #     'md5sum': hashlib.md5(temp.read()).hexdigest()
    #     })
    # logger.debug("data=%s" % data)

    #temp.seek(0)
    r = requests.get(url, headers=headers,
        auth=HTTPBasicAuth(tardis_user, tardis_pass)
        )
    # FIXME: need to check for status_code and handle failures.

    logger.debug("r.js=%s" % r.json)
    logger.debug("r.te=%s" % r.text)
    logger.debug("r.he=%s" % r.headers)
    return r.text


def post_datafile(dest_url, content):
    """
       Do post to mytardis to create new datafile and any exp and dataset if
       needed
    """

    (source_scheme, tardis_host_url, source_path, source_location,
        query_settings) = hrmcstages.parse_bdpurl(dest_url)

    query_settings['mytardis_host'] = tardis_host_url

    logger.debug("query_settings=%s" % query_settings)

    exp_name = hrmcstages.get_value('exp_name', query_settings)
    dataset_name = hrmcstages.get_value('dataset_name', query_settings)
    root_path = hrmcstages.get_value('root_path', query_settings)
    fname = hrmcstages.get_value('fname', query_settings)
    tardis_user = hrmcstages.get_value('mytardis_username', query_settings)
    tardis_pass = hrmcstages.get_value('mytardis_password', query_settings)

    exp_id, _ = get_or_create_experiment(query_settings, exp_name)
    dataset_id, _ = get_or_create_dataset(query_settings, dataset_name, exp_id)

    url = "http://%s/api/v1/dataset_file/" % tardis_host_url
    headers = {'Accept': 'application/json'}
    new_dataset_uri = "/api/v1/dataset/%s/" % dataset_id

    import tempfile
    temp = tempfile.NamedTemporaryFile()
    temp.write(content)
    temp.flush()
    temp.seek(0)

    logger.debug("fname=%s" % fname)
    file_path = os.path.join(root_path, fname)
    logger.debug("file_path=%s" % file_path)
    #logger.debug("content=%s" % open(file_path,'rb').read())
    data = json.dumps({
        'dataset': str(new_dataset_uri),
        'filename': os.path.basename(fname),
        'size': os.stat(temp.name).st_size,
        'mimetype': 'text/plain',
        'md5sum': hashlib.md5(temp.read()).hexdigest()
        })
    logger.debug("data=%s" % data)

    temp.seek(0)
    r = requests.post(url, data={'json_data': data}, headers=headers,
        files={'attached_file': temp},
        auth=HTTPBasicAuth(tardis_user, tardis_pass)
        )
    # FIXME: need to check for status_code and handle failures.

    logger.debug("r.js=%s" % r.json)
    logger.debug("r.te=%s" % r.text)
    logger.debug("r.he=%s" % r.headers)


