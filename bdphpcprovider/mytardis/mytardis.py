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
import hashlib
import re
import json
import requests
from requests.auth import HTTPBasicAuth

from bdphpcprovider import storage

logger = logging.getLogger(__name__)

SCHEMA_PREFIX = "http://rmit.edu.au/schemas"


EXP_DATASET_NAME_SPLIT = 2

# def _get_mytardis_data(tardis_url, field_name):
#     headers = {'content-type': 'application/json'}
#     cookies = {}  # only pulling public info so don't need auth
#     url = "%sapi/v1/%s?limit=0&format=json" % (
#         tardis_url,
#         field_name)
#     logger.debug("url=%s" % url)
#     r = requests.get(url, headers=headers, cookies=cookies)
#     if r.status_code != 200:
#         logger.debug('URL=%s' % url)
#         logger.debug('r.json=%s' % r.json)
#         #logger.debug('r.text=%s' % pformat(r.text))
#         #logger.debug('r.headers=%s' % r.headers)
#         logger.warn("Cannot read %s from %s" % (field_name, tardis_url))
#         return {}
#     return r.json()

# def get_parameter_uri(url, name_uri):
#     res = _get_mytardis_data(url, name_uri + "/")
#     logger.debug("res=%s" % res)
#     if not len(res):
#         return ""
#     else:
#         return res['name']

# def extract_id(uri):
#     if str(uri)[-1] == '/':
#         return str(uri).split('/')[-2:-1][0]
#     else:
#         return str(uri).split('/')[-1]




def _get_value(key, dictionary):
    """
    Return the value for the key in the dictionary, or a blank
    string
    """
    try:
        return dictionary[key]
    except KeyError, e:
        logger.debug(e)
        return u''



def create_graph_paramset(schema_ns, name, graph_info, value_dict, value_keys):
    """
    Construct graph related parameterset

    Notes:

    Args:
        schema_ns: the schema namespace suffix
        name: graph name
        graph_info: attributes for generated graph
        value_dict: attribute values
        value_keys: indexes for read attributes

    Returns:
        Mytardis metadata parameterset format as dict.

    Raises:

    """

    res = {}
    res['schema'] = "%s/%s" % (SCHEMA_PREFIX, schema_ns)
    paramset = []

    def _make_param(x, y):
        param = {}
        param['name'] = x
        param['string_value'] = y
        return param

    for x, y in (
        ("graph_info", json.dumps(graph_info)),
        ("name", name),
        ('value_dict', json.dumps(value_dict)),
        ("value_keys", json.dumps(value_keys))):

        paramset.append(_make_param(x, y))
    res['parameters'] = paramset

    return res


def create_paramset(schema_ns, parameters):
    """
    Construct MyTardis parameterset format

    Args:
        schema_ns:
        parameters:

    Returns:
        Mytardis metadata parameterset format as dict.

    """
    res = {}
    res['schema'] = '%s/%s' % (SCHEMA_PREFIX, schema_ns)
    res['parameters'] = parameters
    return res


def _get_exp_name(settings, url, path):
    """
    Break path based on EXP_DATASET_NAME_SPLIT
    """
    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))


def _get_dataset_name(settings, url, path):
    """
    Break path based on EXP_DATASET_NAME_SPLIT
    """
    logger.debug('dataset_path=%s' % path)
    return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))


def create_experiment(settings, exp_id, expname, experiment_paramset=[]):
    """
        Build Experiment on Remote tardis containing files and metadata

        Notes:
            If exp_id is given, adds to existing experiment, else new created
            and id returned.  experiment_paramset is appended to any
            existing metadata and does not overwrite.
        Args:
            settings.keys():  ['mytardis_user', 'mytardis_password,
                               'mytardis_host']
            exp_id: unique experiment id for existing experiment or 0 for new
            expname: Name for the experiment
            experiment_paramset: Metadata package for experiment parameterset

        Returns:
            New mytardis experiment id

        Raises:
            IndexError if bad settings
    """
    # get existing experiment or create new
    new_exp_id = exp_id
    try:
        tardis_user = settings["mytardis_user"]
        tardis_pass = settings["mytardis_password"]
        tardis_host_url = "http://%s" % settings["mytardis_host"]
    except IndexError, e:
        logger.error(e)
        raise

    logger.debug("experiment_paramset=%s" % experiment_paramset)
    logger.debug(settings)
    exp_id_pat = re.compile(".*/([0-9]+)/$")
    if not new_exp_id:
        logger.debug("creating new experiment")

        url = "%s/api/v1/experiment/?format=json" % tardis_host_url
        headers = {'content-type': 'application/json'}

        data = json.dumps({
        'title': expname,
        'description': 'some test repo',
        "parameter_sets": experiment_paramset,
        })
        logger.debug("data=%s" % data)
        r = requests.post(url,
        data=data,
        headers=headers,
        auth=(tardis_user, tardis_pass))

        # FIXME: need to check for status_code and handle failures such
        # as 500 - lack of disk space at mytardis

        logger.debug('URL=%s' % url)
        logger.debug('r.json=%s' % r.json)
        logger.debug('r.text=%s' % r.text)
        logger.debug('r.headers=%s' % r.headers)

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
        if experiment_paramset:
            logger.debug("updating metadata from existing experiment")

            # exp_obj = _get_mytardis_data(tardis_url, 'experiment/%s' % new_exp_id)

            # sch = schema_info['ns']
            # for parameterset in experiment['parameter_sets']:
            #     sch = parameterset['schema']
            #     parameter_res = {}
            #     for parameter in parameterset['parameters']:
            #         name = get_parameter_name(url, "parametername/%s" % extract_id(parameter['name']))
            #         if not name:
            #             continue
            #         text = parameter['string_value']
            #         parameter_res[name] = text
            #     if parameter_res:
            #         res.append(parameter_res)
            # for pset in experiment_paramset:

            url = "%s/api/v1/experimentparameterset/?format=json" % tardis_host_url
            headers = {'content-type': 'application/json'}

            # TODO: if parameter has already been created, then put rather than
            # post
            for pset in experiment_paramset:
                logger.debug("pset=%s" % pset)
                data = json.dumps(
                   {
                   'experiment': "/api/v1/experiment/%s/" % new_exp_id,
                   'schema': pset['schema'],
                   'parameters': pset['parameters']
                   })
                logger.debug("data=%s" % data)
                r = requests.post(url,
                   data=data,
                   headers=headers,
                   auth=(tardis_user, tardis_pass))

                # FIXME: need to check for status_code and handle failures such
                # as 500 - lack of disk space at mytardis

                logger.debug('URL=%s' % url)
                logger.debug('r.json=%s' % r.json)
                logger.debug('r.text=%s' % r.text)
                logger.debug('r.headers=%s' % r.headers)
    return new_exp_id


def create_dataset(settings,
        source_url,
        exp_id,
        exp_name=_get_exp_name,
        dataset_name=_get_dataset_name,
        experiment_paramset=[],
        dataset_paramset=[],
        datafile_paramset=[],
        dfile_extract_func=None):
    """

    Notes:
        POST to mytardis_host REST API with mytardis_user and mytardis_password
        credentials to create or update experiment for a new dataset containing
        datafiles from source_url BDP directory.

    Args:
        settings:

        source_url: url containing data to be ingested
        exp_id:
        [exp_name,dataset_name]:  functions that return new
    experiment and dataset names respectively based on url and path
        experiment_paramset: ...
        dataset_paramset: ...
        datafile_paramset:
        dfile_extract_func:


    FIXME,TODO: What if tardis in unavailable?  Connection to mytardis probably
    better handled as sperate celery subtask, which can retry until working and
    be async

    FIXME: missing all error checking and retrying of connection to mytardis.
    Reliability framework should be able to supply this?
    """

    #TODO: method should take BDP url source_url not, expanded one.

    logger.debug("post_dataset")
    tardis_user = settings["mytardis_user"]
    tardis_pass = settings["mytardis_password"]
    tardis_host_url = "http://%s" % settings["mytardis_host"]
    logger.debug("posting dataset from %s to mytardis at %s with %s" % (source_url,
        tardis_host_url, tardis_pass))

    (source_scheme, source_location, source_path, source_location,
        query_settings) = storage.parse_bdpurl(source_url)

    logger.debug("source_path=%s" % source_path)

    if source_scheme == "file":
        root_path = _get_value('root_path', query_settings)
    else:
        logger.debug('schema=%s' % source_scheme)
        #raise InvalidInputError("only file source_schema supported for source of mytardis transfer")

    expname = exp_name(settings, source_url, source_path)
    new_exp_id = create_experiment(settings, exp_id, expname, experiment_paramset)

    new_experiment_uri = "/api/v1/experiment/%s/" % new_exp_id

    # TODO: check that we do not alreay have a dataset with
    # the same name and overwrite or don't move.
    # save dataset
    logger.debug("saving dataset in experiment at %s" % new_exp_id)
    url = "%s/api/v1/dataset/?format=json" % tardis_host_url
    headers = {'content-type': 'application/json'}

    # # FIXME: schema should be a parameter
    # schemas = [{
    #            "schema": "http://rmit.edu.au/schemas/hrmcdataset",
    #            "parameters": []
    #           }]
    # if dataset_schema:
    #    schemas.append({
    #        "schema": dataset_schema,
    #        "parameters": []
    #        })

    schemas = dataset_paramset

    logger.debug("schemas=%s" % schemas)
    data = json.dumps({
       'experiments': [new_experiment_uri],
       'description': dataset_name(settings, source_url, source_path),
       "parameter_sets": schemas
           })
    logger.debug("data=%s" % data)
    logger.debug("post to %s" % url)
    r = requests.post(url, data=data, headers=headers, auth=HTTPBasicAuth(tardis_user, tardis_pass))
    # FIXME: need to check for status_code and handle failures.

    logger.debug("r.json=%s" % r.json)
    logger.debug("r.text=%s" % r.text)
    logger.debug("r.headers=%s" % r.headers)
    header_location = r.headers['location']
    new_dataset_uri = header_location[len(tardis_host_url):]

    # move files across
    source_files = storage.list_all_files(source_url)
    logger.debug("source_files=%s" % source_files)
    url = "%s/api/v1/dataset_file/" % tardis_host_url
    headers = {'Accept': 'application/json'}

    args = source_url.split('?')[1]

    logger.debug('args=%s' % args)
    '''
    psd_url = smartconnector.get_url_with_pkey(output_storage_credentials,
                        'ssh://unix@' + os.path.join(self.output_dir,
                            node_output_dir, "PSD_output", "psd.dat"), is_relative_path=False)
        logger.debug('psd_url=%s' % psd_url)

        psd = hrmcstages.storage.get_filep(psd_url)
    '''
    for file_location in source_files:
        logger.debug('file_location=%s' % os.path.join(source_location, file_location))
        source_file_url = "%s://%s?%s" % (source_scheme, os.path.join(source_location, file_location), args)
        logger.debug('source_file_url=%s' % source_file_url)
        source_file, source_file_ref = storage.get_filep(source_file_url, sftp_reference=True)
        logger.debug('source_file=%s' % source_file._name)
        #file_path = os.path.join(root_path, file_location)
        #file_path = os.path.join(source_url, file_location)
        #logger.debug("file_path=%s" % file_path)
        #logger.debug("content=%s" % open(file_path,'rb').read())

        new_datafile_paramset = []
        logger.debug("datafile_paramset=%s" % datafile_paramset)
        for paramset in datafile_paramset:
            new_paramset = {}
            logger.debug("paramset=%s" % paramset)
            new_paramset['schema'] = paramset['schema']

            has_value = False
            has_keys = False
            new_param_vals = []
            for param in paramset['parameters']:
                new_param = {}
                for param_key, v in param.items():

                    if param_key == 'name' and v == "value_dict":
                        new_param['name'] = 'value_dict'
                        new_value = {}

                        #val = param['string_value']

                        # if not isinstance(val, basestring):
                        #     dfile_extract_func = val

                        found_func_match = False
                        for fname, func in dfile_extract_func.items():
                            logger.debug("fname=%s,func=%s" % (fname, func))
                            if fname == os.path.basename(file_location):
                                #new_value.update(func(open(file_path, 'r')))
                                source_file.seek(0)
                                new_value.update(func(source_file))

                                found_func_match = True  # FIXME: can multiple funcs match?

                        logger.debug("new_value=%s" % new_value)

                        if found_func_match:
                            new_param['string_value'] = json.dumps(new_value)
                        else:
                            new_param['string_value'] = param['string_value']
                        break
                    else:
                        # incase string_value is processed first
                        new_param[param_key] = v

                if new_param['name'] == "value_dict" and len(json.loads(new_param['string_value'])):
                    has_value = True
                if new_param['name'] == "value_keys" and len(json.loads(new_param['string_value'])):
                    has_keys = True
                new_param_vals.append(new_param)

            new_paramset['parameters'] = new_param_vals

            logger.debug("has_value=%s" % has_value)
            logger.debug("has_keys=%s" % has_keys)

            if has_value or has_keys:
                new_datafile_paramset.append(new_paramset)
            else:
                logger.debug("not adding %s" % new_paramset)

        logger.debug("new_datafile_paramset=%s" % new_datafile_paramset)
        logger.debug("file_namee=%s" % source_file._name)
        file_size = source_file_ref.size(source_file._name)
        logger.debug("file_size=%s" % file_size)
        if file_size > 0:
            source_file.seek(0)
            data = json.dumps({
                'dataset': str(new_dataset_uri),
                "parameter_sets": new_datafile_paramset,
                'filename': os.path.basename(file_location),
                #'filename': os.path.basename(file_path),
                'size': file_size,
                'mimetype': 'text/plain',
                'md5sum': hashlib.md5(source_file.read()).hexdigest()
                #'md5sum': hashlib.md5(open(file_path, 'r').read()).hexdigest()
                })
            logger.debug("data=%s" % data)
            #import pdb; pdb.set_trace()
            source_file.seek(0)
            #logger.debug(source_file.read())
            source_file.seek(0)
            r = requests.post(url, data={'json_data': data}, headers=headers,
                files={'attached_file': source_file},  # open(file_path, 'rb')},
                auth=HTTPBasicAuth(tardis_user, tardis_pass)
                )

            # FIXME: need to check for status_code and handle failures.

            logger.debug("r.js=%s" % r.json)
            logger.debug("r.te=%s" % r.text)
            logger.debug("r.he=%s" % r.headers)
        else:
            logger.warn("not transferring empty file %s" % file_location)
            #TODO: check whether mytardis api can accept zero length files

    return new_exp_id


def retrieve_datafile(url):
    """
    Retrieve contents from a mytardis datafile based on url

    NB: Has this function been tested?

    """

    (source_scheme, tardis_host_url, source_path, source_location,
        query_settings) = storage.parse_bdpurl(url)

    query_settings['mytardis_host'] = tardis_host_url

    logger.debug("query_settings=%s" % query_settings)

    exp_name = _get_value('exp_name', query_settings)
    dataset_name = _get_value('dataset_name', query_settings)
    root_path = _get_value('root_path', query_settings)
    fname = _get_value('fname', query_settings)
    tardis_user = _get_value('mytardis_username', query_settings)
    tardis_pass = _get_value('mytardis_password', query_settings)

    exp_id, _ = _get_or_create_experiment(query_settings, exp_name)
    dataset_id, _ = _get_or_create_dataset(query_settings, dataset_name, exp_id)

    url = "http://%s/api/v1/dataset_file/%s/" % (tardis_host_url, dataset_id)
    headers = {'Accept': 'application/json'}

    logger.debug("fname=%s" % fname)
    # file_path = os.path.join(root_path, fname)
    # logger.debug("file_path=%s" % file_path)
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

    # logger.debug("r.js=%s" % r.json)
    # logger.debug("r.te=%s" % r.text)
    # logger.debug("r.he=%s" % r.headers)
    return r.text

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


def _get_or_create_experiment(query_settings, exp_name):

    headers = {'content-type': 'application/json'}
    tardis_user = query_settings["mytardis_username"]
    tardis_pass = query_settings["mytardis_password"]
    tardis_host_url = "http://%s" % query_settings["mytardis_host"]
    tardis_url = "%s/api/v1/experiment/?limit=0&format=json" % tardis_host_url
    r = requests.get(tardis_url, headers=headers, auth=(tardis_user, tardis_pass))
    # logger.debug(r.json)
    # logger.debug(r.text)
    # logger.debug(r.headers)
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

        # logger.debug(r.json)
        # logger.debug(r.text)
        # logger.debug(r.headers)
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


def _get_or_create_dataset(settings, dataset_name, exp_id, dataset_schema=None):
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

        # logger.debug("r.json=%s" % r.json)
        # logger.debug("r.text=%s" % r.text)
        # logger.debug("r.headers=%s" % r.headers)

        return (_extract_id_from_location(dataset_name, r), True)

    else:
        return (ids[0], False)


def _post_datafile(dest_url, content):
    """
       Do post to mytardis to create new datafile and any exp and dataset if
       needed
    """

    (source_scheme, tardis_host_url, source_path, source_location,
        query_settings) = storage.parse_bdpurl(dest_url)

    query_settings['mytardis_host'] = tardis_host_url

    logger.debug("query_settings=%s" % query_settings)

    exp_name = _get_value('exp_name', query_settings)
    dataset_name = _get_value('dataset_name', query_settings)
    root_path = _get_value('root_path', query_settings)
    fname = _get_value('fname', query_settings)
    tardis_user = _get_value('mytardis_username', query_settings)
    tardis_pass = _get_value('mytardis_password', query_settings)

    exp_id, _ = _get_or_create_experiment(query_settings, exp_name)
    dataset_id, _ = _get_or_create_dataset(query_settings, dataset_name, exp_id)

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

    # logger.debug("r.js=%s" % r.json)
    # logger.debug("r.te=%s" % r.text)
    # logger.debug("r.he=%s" % r.headers)



