
import os, re, sys
import ast
import json
import logging
from collections import namedtuple
import fnmatch


from boto.exception import EC2ResponseError
from django.core.files.base import ContentFile
from chiminey.platform import manage
from chiminey import storage
from chiminey.sshconnection import open_connection, AuthError
from chiminey.compute import run_command_with_status
from chiminey.cloudconnection import \
    create_ssh_security_group, create_key_pair
from chiminey.platform.validate import validate_mytardis_parameters
from chiminey.mytardis import mytardis

from chiminey.mytardis.mytardis import create_paramset
from chiminey.storage import get_url_with_credentials
from chiminey.runsettings import getval, SettingNotFoundException
from chiminey.smartconnectorscheduler.errors import BadInputException
from django.conf import settings as django_settings


RMIT_SCHEMA = django_settings.SCHEMA_PREFIX
DATA_ERRORS_FILE = "data_errors.dat"
STEP_COLUMN_NUM = 0
ERRGR_COLUMN_NUM = 28



logger = logging.getLogger(__name__)


class MyTardisPlatform():
    VALUES_FNAME = "values"
    SCHEMA_PREFIX = django_settings.SCHEMA_PREFIX

    def get_platform_types(self):
        return ['mytardis']

    def configure(self, platform_type, username, parameters):
        #def configure_unix_platform(platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        key_relative_path = os.path.join(
            '.ssh', username, platform_type, key_name)
        parameters['private_key_path'] = key_relative_path

    def validate(self, parameters, passwd_auth=False):
        return [False] + list(validate_mytardis_parameters(parameters))

    def generate_key(self, parameters):
        return "no key", ""

    # def get_platform_settings(self, platform_url, username):
    #     platform_name = platform_url.split('/')[0]
    #     if platform_name == "local":
    #         return {"scheme": 'file', 'type': 'local', 'host': '127.0.0.1'}
    #     record, schema_namespace = retrieve_platform(platform_name, username)
    #     logger.debug("record=%s" % record)
    #     logger.debug("schema_namespace=%s" % schema_namespace)
    #     _update_platform_settings(record)
    #     record['bdp_username'] = username
    #     return record

    def update_platform_settings(self, settings):
        try:
            platform_type = settings['platform_type']
        except KeyError:
            logger.error("settings=%s" % settings)
            raise
        settings['type'] = platform_type
        if platform_type == 'mytardis':
            settings['mytardis_host'] = settings['ip_address']
            settings['mytardis_user'] = settings['username']
            settings['mytardis_password'] = settings['password']


    def curate_configured_data(self, run_settings, location, experiment_id):
        bdp_username = run_settings['http://rmit.edu.au/schemas/bdp_userprofile']['username']

        curate_data = run_settings['http://rmit.edu.au/schemas/input/mytardis']['curate_data']
        if curate_data:
            mytardis_url = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
            logger.debug(mytardis_settings)

            EXP_DATASET_NAME_SPLIT = 2

            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            logger.debug("location=%s" % location)
            ename = _get_exp_name_for_input(location)
            logger.debug("ename=%s" % ename)
            experiment_id = mytardis.create_experiment(
                settings=mytardis_settings,
                exp_id=experiment_id,
                expname=ename,
                experiment_paramset=[ #TODO: MYTARDIS
                    #mytardis.create_paramset("hrmcexp", []),
                    #mytardis.create_graph_paramset("expgraph",
                    #    name="hrmcexp",
                    #    graph_info={"axes":["iteration", "criterion"], "legends":["criterion"], "precision":[0, 2]},
                    #    value_dict={},
                    #    value_keys=[["hrmcdset/it", "hrmcdset/crit"]])
            ])

        else:
            logger.warn('Data curation is off')
        return experiment_id


    def curate_input_data(self, experiment_id, local_settings, output_storage_settings,
                    mytardis_settings, source_files_url):
        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        output_host = output_storage_settings['host']

        EXP_DATASET_NAME_SPLIT = 2

        def _get_exp_name_for_input(settings, url, path):
            return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

        def _get_dataset_name_for_input(settings, url, path):
            VALUES_FNAME = "values" #TODO: Mytardis, move to settings
            logger.debug("path=%s" % path)
            source_url = get_url_with_credentials(
                output_storage_settings,
                output_prefix + os.path.join(output_host, path, VALUES_FNAME),
                is_relative_path=False)
            logger.debug("source_url=%s" % source_url)
            try:
                content = storage.get_file(source_url)
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
        experiment_id = mytardis.create_dataset(
            settings=local_settings,
            source_url=source_files_url,
            exp_id=experiment_id,
            exp_name=_get_exp_name_for_input,
            dataset_name=_get_dataset_name_for_input,
            experiment_paramset=[],
            dataset_paramset=[#TODO: MYTARDIS
                #create_paramset('hrmcdataset/input', [])
                ])
        return experiment_id

    def curate_transformed_dataset(self, run_settings, experiment_id, base_dir, output_url,
        all_settings, outputs=[]):
        logger.debug('self_outpus_curate=%s' % outputs)
        iteration = int(getval(run_settings, '%s/system/id' % self.SCHEMA_PREFIX))
        iter_output_dir = os.path.join(os.path.join(base_dir, "output_%s" % iteration))
        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)

        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        fsys = storage.get_filesystem(output_url)

        node_output_dirnames, _ = fsys.listdir(mypath)
        logger.debug("node_output_dirnames=%s" % node_output_dirnames)

        if all_settings['mytardis_host']:
            for i, node_output_dirname in enumerate(node_output_dirnames):
                node_path = os.path.join(iter_output_dir, node_output_dirname)
                # find criterion
                crit = None  # is there an infinity criterion
                for ni in outputs:
                    if ni.dirname == node_output_dirname:
                        crit = ni.criterion
                        break
                else:
                    logger.debug("criterion not found")
                    continue
                logger.debug("crit=%s" % crit)

                # graph_params = []

                def extract_psd_func(fp):
                    res = []
                    xs = []
                    ys = []
                    for i, line in enumerate(fp):
                        columns = line.split()
                        xs.append(float(columns[0]))
                        ys.append(float(columns[1]))
                    res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
                    return res

                def extract_psdexp_func(fp):
                    res = []
                    xs = []
                    ys = []
                    for i, line in enumerate(fp):
                        columns = line.split()
                        xs.append(float(columns[0]))
                        ys.append(float(columns[1]))
                    res = {"hrmcdfile/r2": xs, "hrmcdfile/g2": ys}
                    return res

                def extract_grfinal_func(fp):
                    res = []
                    xs = []
                    ys = []
                    for i, line in enumerate(fp):
                        columns = line.split()
                        xs.append(float(columns[0]))
                        ys.append(float(columns[1]))
                    #FIXME: len(xs) == len(ys) for this to work.
                    #TODO: hack to handle when xs and ys are too
                    # large to fit in Parameter with db_index.
                    # solved by function call at destination
                    cut_xs = [xs[i] for i, x in enumerate(xs)
                        if (i % (len(xs) / 20) == 0)]
                    cut_ys = [ys[i] for i, x in enumerate(ys)
                        if (i % (len(ys) / 20) == 0)]

                    res = {"hrmcdfile/r3": cut_xs, "hrmcdfile/g3": cut_ys}
                    return res

                def extract_inputgr_func(fp):
                    res = []
                    xs = []
                    ys = []
                    for i, line in enumerate(fp):
                        columns = line.split()
                        xs.append(float(columns[0]))
                        ys.append(float(columns[1]))
                    #FIXME: len(xs) == len(ys) for this to work.
                    #TODO: hack to handle when xs and ys are too
                    # large to fit in Parameter with db_index.
                    # solved by function call at destination
                    cut_xs = [xs[i] for i, x in enumerate(xs)
                        if (i % (len(xs) / 20) == 0)]
                    cut_ys = [ys[i] for i, x in enumerate(ys)
                        if (i % (len(ys) / 20) == 0)]

                    res = {"hrmcdfile/r4": cut_xs, "hrmcdfile/g4": cut_ys}
                    return res

                #TODO: hrmcexp graph should be tagged to input directories (not output directories)
                #because we want the result after pruning.
                #todo: replace self.boto_setttings with mytardis_settings

                EXP_DATASET_NAME_SPLIT = 2

                def get_exp_name_for_output(settings, url, path):
                    # return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))
                    return str(os.sep.join(path.split(os.sep)[-4:-2]))

                def get_dataset_name_for_output(settings, url, path):
                    logger.debug("path=%s" % path)

                    host = settings['host']
                    prefix = 'ssh://%s@%s' % (settings['type'], host)
                    VALUES_FNAME = "values" #TODO: Mytardis, move to settings
                    source_url = get_url_with_credentials(
                        settings, os.path.join(prefix, path, VALUES_FNAME),
                        is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)
                    try:
                        content = storage.get_file(source_url)
                    except IOError, e:
                        logger.warn("cannot read file %s" % e)
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
                        iteration = "final"

                    dataset_name = "%s_%s_%s" % (iteration,
                        values_map['generator_counter'],
                        values_map['run_counter'])
                    logger.debug("dataset_name=%s" % dataset_name)
                    return dataset_name

                source_dir_url = get_url_with_credentials(
                    all_settings,
                    node_path,
                    is_relative_path=False)
                logger.debug("source_dir_url=%s" % source_dir_url)
                logger.debug('all_settings_here=%s' % all_settings)
                system_id = int(getval(run_settings, '%s/system/id' % self.SCHEMA_PREFIX)) #TODO Mytardis
                experiment_id = mytardis.create_dataset(
                    settings=all_settings,
                    source_url=source_dir_url,
                    exp_id=experiment_id,
                    exp_name=get_exp_name_for_output,
                    dataset_name=get_dataset_name_for_output)
                #TODO Mytardis
                '''
                experiment_id = mytardis.create_dataset(
                    settings=all_settings,
                    source_url=source_dir_url,
                    exp_id=experiment_id,
                    exp_name=get_exp_name_for_output,
                    dataset_name=get_dataset_name_for_output,
                    dataset_paramset=[
                        mytardis.create_paramset("hrmcdataset/output", []),
                        mytardis.create_graph_paramset("dsetgraph",
                            name="hrmcdset",
                            graph_info={"axes":["r (Angstroms)", "PSD"],
                                "legends":["psd", "PSD_exp"], "type":"line"},
                            value_dict={"hrmcdset/it": system_id,
                                 "hrmcdset/crit": crit},
                            value_keys=[["hrmcdfile/r1", "hrmcdfile/g1"],
                                ["hrmcdfile/r2", "hrmcdfile/g2"]]
                            ),
                        mytardis.create_graph_paramset("dsetgraph",
                            name="hrmcdset2",
                            graph_info={"axes":["r (Angstroms)", "g(r)"],
                                "legends":["data_grfinal", "input_gr"],
                                "type":"line"},
                            value_dict={},
                            value_keys=[["hrmcdfile/r3", "hrmcdfile/g3"],
                                ["hrmcdfile/r4", "hrmcdfile/g4"]]
                            ),
                        ],
                   datafile_paramset=[
                        mytardis.create_graph_paramset("dfilegraph",
                            name="hrmcdfile",
                            graph_info={},
                            value_dict={},
                            value_keys=[])
                        ],
                   # TODO: move extract function into paramset structure
                   dfile_extract_func={ #TODO Mytardis
                        'psd.dat': extract_psd_func,
                        'PSD_exp.dat': extract_psdexp_func,
                        'data_grfinal.dat': extract_grfinal_func,
                        'input_gr.dat': extract_inputgr_func

                        }

                   )
                '''

        else:
            logger.warn("no mytardis host specified")
            return 0
        return experiment_id


    def curate_converged_dataset(self, run_settings, experiment_id, base_dir, output_url, all_settings):
        logger.debug("curate_dataset")
        iter_output_dir = os.path.join(os.path.join(base_dir, "output"))
        logger.debug("iter_output_dir=%s" % iter_output_dir)

        output_prefix = '%s://%s@' % (all_settings['scheme'],
                                    all_settings['type'])
        iter_output_dir = "%s%s" % (output_prefix, iter_output_dir)
        logger.debug("iter_output_dir=%s" % iter_output_dir)
        logger.debug("output_url=%s" % output_url)
        (scheme, host, mypath, location, query_settings) = storage.parse_bdpurl(output_url)
        fsys = storage.get_filesystem(output_url)

        node_output_dirnames, _ = fsys.listdir(mypath)
        logger.debug("node_output_dirnames=%s" % node_output_dirnames)

        curate_data = (getval(run_settings, '%s/input/mytardis/curate_data' % self.SCHEMA_PREFIX))
        if curate_data:
            if all_settings['mytardis_host']:

#         if mytardis_settings['mytardis_host']:

#             EXP_DATASET_NAME_SPLIT = 2

#             def get_exp_name_for_output(settings, url, path):
#                 return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

#             def get_dataset_name_for_output(settings, url, path):
#                 logger.debug("path=%s" % path)

#                 host = settings['host']
#                 prefix = 'ssh://%s@%s' % (settings['type'], host)

#                 source_url = smartconnectorscheduler.get_url_with_credentials(
#                     settings, os.path.join(prefix, path, "HRMC.inp_values"),
#                     is_relative_path=False)
#                 logger.debug("source_url=%s" % source_url)
#                 try:
#                     content = storage.get_file(source_url)
#                 except IOError, e:
#                     logger.warn("cannot read file %s" % e)
#                     return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

#                 logger.debug("content=%s" % content)
#                 try:
#                     values_map = dict(json.loads(str(content)))
#                 except Exception, e:
#                     logger.error("cannot load values_map %s: from %s.  Error=%s" % (content, source_url, e))
#                     return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

#                 try:
#                     iteration = str(path.split(os.sep)[-2:-1][0])
#                 except Exception, e:
#                     logger.error(e)
#                     iteration = ""

#                 if "_" in iteration:
#                     iteration = iteration.split("_")[1]
#                 else:
#                     iteration = "final"

#                 dataset_name = "%s_%s_%s" % (iteration,
#                     values_map['generator_counter'],
#                     values_map['run_counter'])
#                 logger.debug("dataset_name=%s" % dataset_name)
#                 return dataset_name

#             re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

#             logger.debug("new_output_dir=%s" % new_output_dir)
#             exp_value_keys = []
#             legends = []
#             for m, node_dir in enumerate(node_dirs):
#                 exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

#                 source_url = smartconnectorscheduler.get_url_with_credentials(output_storage_settings,
#                     output_prefix + os.path.join(new_output_dir, node_dir), is_relative_path=False)

#                 (source_scheme, source_location, source_path, source_location,
#                     query_settings) = storage.parse_bdpurl(source_url)
#                 logger.debug("source_url=%s" % source_url)
#                 legends.append(
#                     get_dataset_name_for_output(
#                         output_storage_settings, "", source_path))

#             logger.debug("exp_value_keys=%s" % exp_value_keys)
#             logger.debug("legends=%s" % legends)

#             graph_paramset = [mytardis.create_graph_paramset("expgraph",
#                 name="hrmcexp2",
#                 graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
#                 value_dict={},
#                 value_keys=exp_value_keys)]

#             for m, node_dir in enumerate(node_dirs):

#                 dataerrors_url = smartconnectorscheduler.get_url_with_credentials(output_storage_settings,
#                     output_prefix + os.path.join(new_output_dir, node_dir, DATA_ERRORS_FILE), is_relative_path=False)
#                 dataerrors_content = storage.get_file(dataerrors_url)
#                 xs = []
#                 ys = []
#                 for i, line in enumerate(dataerrors_content.splitlines()):
#                     if i == 0:
#                         continue
#                     columns = line.split()
#                     try:
#                         hrmc_step = int(columns[STEP_COLUMN_NUM])
#                     except ValueError:
#                         logger.warn("could not parse hrmc_step value on line %s" % i)
#                         continue
#                     # handle  format double precision float format
#                     val = columns[ERRGR_COLUMN_NUM]
#                     val = re_dbl_fort.sub(r'\1E\2', val)
#                     logger.debug("val=%s" % val)





                EXP_DATASET_NAME_SPLIT = 2

                def get_exp_name_for_output(settings, url, path):
                    return str(os.sep.join(path.split(os.sep)[:-EXP_DATASET_NAME_SPLIT]))

                def get_dataset_name_for_output(settings, url, path):
                    logger.debug("path=%s" % path)

                    host = settings['host']
                    prefix = 'ssh://%s@%s' % (settings['type'], host)
                    VALUES_FNAME = "values" #TODO: Mytardis, move to settings
                    source_url = get_url_with_credentials(
                        settings, os.path.join(prefix, path, VALUES_FNAME),
                        is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)
                    try:
                        content = storage.get_file(source_url)
                    except IOError, e:
                        logger.warn("cannot read file %s" % e)
                        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    logger.debug("content=%s" % content)
                    try:
                        values_map = dict(json.loads(str(content)))
                    except Exception, e:
                        logger.error("cannot load values_map %s: from %s.  Error=%s" % (content, source_url, e))
                        return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    try:
                        iteration = str(path.split(os.sep)[-2:-1][0])
                    except Exception, e:
                        logger.error(e)
                        iteration = ""

                    if "_" in iteration:
                        iteration = iteration.split("_")[1]
                    else:
                        iteration = "final"

                    dataset_name = "%s_%s_%s" % (iteration,
                        values_map['generator_counter'],
                        values_map['run_counter'])
                    logger.debug("dataset_name=%s" % dataset_name)
                    return dataset_name

                re_dbl_fort = re.compile(r'(\d*\.\d+)[dD]([-+]?\d+)')

                exp_value_keys = []
                legends = []
                for m, node_dir in enumerate(node_output_dirnames):
                    node_path = os.path.join(iter_output_dir, node_dir)

                    exp_value_keys.append(["hrmcdset%s/step" % m, "hrmcdset%s/err" % m])

                    source_url = get_url_with_credentials(all_settings,
                                                   node_path, is_relative_path=False)

                    (source_scheme, source_location, source_path, source_location,
                        query_settings) = storage.parse_bdpurl(source_url)
                    logger.debug("source_url=%s" % source_url)
                    legends.append(
                        get_dataset_name_for_output(
                            all_settings, "", source_path))

                logger.debug("exp_value_keys=%s" % exp_value_keys)
                logger.debug("legends=%s" % legends)

                graph_paramset = [mytardis.create_graph_paramset("expgraph",
                    name="hrmcexp2",
                    graph_info={"axes": ["step", "ERRGr*wf"], "precision": [0, 2], "legends": legends},
                    value_dict={},
                    value_keys=exp_value_keys)]

                for m, node_dir in enumerate(node_output_dirnames):
                    node_path = os.path.join(iter_output_dir, node_dir)
                    logger.debug("node_path=%s" % node_path)

                    #FIXME: this calculation should be done as in extract_psd_func
                    # pulling directly from data_errors rather than passing in
                    # through nested function.
                    dataerrors_url = get_url_with_credentials(all_settings,
                        os.path.join(node_path, DATA_ERRORS_FILE),
                        is_relative_path=False)
                    logger.debug("dataerrors_url=%s" % dataerrors_url)
                    dataerrors_content = storage.get_file(dataerrors_url)
                    xs = []
                    ys = []
                    for i, line in enumerate(dataerrors_content.splitlines()):
                        if i == 0:
                            continue
                        columns = line.split()
                        try:
                            hrmc_step = int(columns[STEP_COLUMN_NUM])
                        except ValueError:
                            logger.warn("could not parse hrmc_step value on line %s" % i)
                            continue
                        # handle  format double precision float format
                        val = columns[ERRGR_COLUMN_NUM]
                        val = re_dbl_fort.sub(r'\1E\2', val)
                        logger.debug("val=%s" % val)
                        try:
                            hrmc_errgr = float(val)
                        except ValueError:
                            logger.warn("could not parse hrmc_errgr value on line %s" % i)
                            continue
                        xs.append(hrmc_step)
                        ys.append(hrmc_errgr)

                    logger.debug("xs=%s" % xs)
                    logger.debug("ys=%s" % ys)

                    crit_url = get_url_with_credentials(all_settings,
                        os.path.join(node_path, "criterion.txt"), is_relative_path=False)
                    try:
                        crit = storage.get_file(crit_url)
                    except ValueError:
                        crit = None
                    except IOError:
                        crit = None
                    # FIXME: can crit be zero?
                    if crit:
                        hrmcdset_val = {"hrmcdset/it": self.id, "hrmcdset/crit": crit}
                    else:
                        hrmcdset_val = {}

                    source_url = get_url_with_credentials(
                        all_settings, node_path, is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)

                    # TODO: move into utiltiy function for reuse
                    def extract_psd_func(fp):
                        res = []
                        xs = []
                        ys = []
                        for i, line in enumerate(dataerrors_content.splitlines()):
                            if i == 0:
                                continue
                            columns = line.split()

                            val = columns[STEP_COLUMN_NUM]
                            val = re_dbl_fort.sub(r'\1E\2', val)
                            logger.debug("val=%s" % val)
                            try:
                                x = float(val)
                            except ValueError:
                                logger.warn("could not parse value on line %s" % i)
                                continue

                            val = columns[ERRGR_COLUMN_NUM]
                            val = re_dbl_fort.sub(r'\1E\2', val)
                            logger.debug("val=%s" % val)
                            try:
                                y = float(val)
                            except ValueError:
                                logger.warn("could not parse value on line %s" % i)
                                continue

                            xs.append(x)
                            ys.append(y)
                        res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
                        return res

                    def extract_psdexp_func(fp):
                        res = []
                        xs = []
                        ys = []
                        for i, line in enumerate(fp):
                            columns = line.split()
                            xs.append(float(columns[0]))
                            ys.append(float(columns[1]))
                        res = {"hrmcdfile/r2": xs, "hrmcdfile/g2": ys}
                        return res

                    def extract_grfinal_func(fp):
                        res = []
                        xs = []
                        ys = []
                        for i, line in enumerate(fp):
                            columns = line.split()
                            xs.append(float(columns[0]))
                            ys.append(float(columns[1]))
                        #FIXME: len(xs) == len(ys) for this to work.
                        #TODO: hack to handle when xs and ys are too
                        # large to fit in Parameter with db_index.
                        # solved by function call at destination
                        cut_xs = [xs[i] for i, x in enumerate(xs)
                            if (i % (len(xs) / 20) == 0)]
                        cut_ys = [ys[i] for i, x in enumerate(ys)
                            if (i % (len(ys) / 20) == 0)]

                        res = {"hrmcdfile/r3": cut_xs, "hrmcdfile/g3": cut_ys}
                        return res

                    def extract_inputgr_func(fp):
                        res = []
                        xs = []
                        ys = []
                        for i, line in enumerate(fp):
                            columns = line.split()
                            xs.append(float(columns[0]))
                            ys.append(float(columns[1]))
                        #FIXME: len(xs) == len(ys) for this to work.
                        #TODO: hack to handle when xs and ys are too
                        # large to fit in Parameter with db_index.
                        # solved by function call at destination
                        cut_xs = [xs[i] for i, x in enumerate(xs)
                            if (i % (len(xs) / 20) == 0)]
                        cut_ys = [ys[i] for i, x in enumerate(ys)
                            if (i % (len(ys) / 20) == 0)]

                        res = {"hrmcdfile/r4": cut_xs, "hrmcdfile/g4": cut_ys}
                        return res
                    #todo: replace self.boto_setttings with mytardis_settings
                    #TODO Mytardis
                    '''
                    experiment_id = mytardis.create_dataset(
                        settings=all_settings,
                        source_url=source_url,
                        exp_name=get_exp_name_for_output,
                        dataset_name=get_dataset_name_for_output,
                        exp_id=experiment_id,
                        experiment_paramset=graph_paramset,
                        dataset_paramset=[
                            mytardis.create_paramset('hrmcdataset/output', []),
                            mytardis.create_graph_paramset('dsetgraph',
                                name="hrmcdset",
                                graph_info={"axes":["r (Angstroms)", "PSD"],
                                    "legends":["psd", "PSD_exp"],  "type":"line"},
                                value_dict=hrmcdset_val,
                                value_keys=[["hrmcdfile/r1", "hrmcdfile/g1"],
                                    ["hrmcdfile/r2", "hrmcdfile/g2"]]),
                            mytardis.create_graph_paramset('dsetgraph',
                                name='hrmcdset2',
                                graph_info={"axes":["r (Angstroms)", "g(r)"],
                                    "legends":["data_grfinal", "input_gr"],
                                    "type":"line"},
                                value_dict={},
                                value_keys=[["hrmcdfile/r3", "hrmcdfile/g3"],
                                    ["hrmcdfile/r4", "hrmcdfile/g4"]]),
                            mytardis.create_graph_paramset('dsetgraph',
                                name='hrmcdset%s' % m,
                                graph_info={},
                                value_dict={"hrmcdset%s/step" % m: xs,
                                    "hrmcdset%s/err" % m: ys},
                                value_keys=[]),
                            ],
                        datafile_paramset=[
                            mytardis.create_graph_paramset('dfilegraph',
                                name="hrmcdfile",
                                graph_info={},
                                value_dict={},
                                value_keys=[])
                            ],
                        dfile_extract_func={
                            'psd.dat': extract_psd_func,
                             'PSD_exp.dat': extract_psdexp_func,
                             'data_grfinal.dat': extract_grfinal_func,
                             'input_gr.dat': extract_inputgr_func}

                        )
                    '''
                    experiment_id = mytardis.create_dataset(
                        settings=all_settings,
                        source_url=source_url,
                        exp_name=get_exp_name_for_output,
                        dataset_name=get_dataset_name_for_output,
                        exp_id=experiment_id,
                        experiment_paramset=graph_paramset)
                    graph_paramset = []
            else:
                logger.warn("no mytardis host specified")
        else:
            logger.warn('Data curation is off')
        return experiment_id
