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
from chiminey.smartconnectorscheduler import jobs

from chiminey.mytardis.mytardis import create_paramset
from chiminey.storage import get_url_with_credentials
from chiminey.runsettings import getval, SettingNotFoundException
from chiminey.smartconnectorscheduler.errors import BadInputException
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured


RMIT_SCHEMA = django_settings.SCHEMA_PREFIX

logger = logging.getLogger(__name__)


class MyTardisPlatform():
    VALUES_FNAME = django_settings.VALUES_FNAME
    SCHEMA_PREFIX = django_settings.SCHEMA_PREFIX
    METADATA_BUILDER = None

    def load_metadata_builder(self, run_settings):
        if not self.METADATA_BUILDER:
            try:
                self.METADATA_BUILDER = jobs.safe_import(run_settings['%s/system' %  \
                django_settings.SCHEMA_PREFIX]['metadata_builder'], [], {})
            except ImproperlyConfigured as  e:
                logger.warn("Cannot load metadata builder class %s \n" % e)


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


    def create_experiment(self, run_settings, location, experiment_id):
        bdp_username = run_settings['%s/bdp_userprofile' % django_settings.SCHEMA_PREFIX]['username']

        curate_data = run_settings['%s/input/mytardis' % django_settings.SCHEMA_PREFIX]['curate_data']
        if curate_data:
            mytardis_url = run_settings['%s/input/mytardis' % django_settings.SCHEMA_PREFIX]['mytardis_platform']
            mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
            logger.debug(mytardis_settings)

            EXP_DATASET_NAME_SPLIT = 2

            def _get_exp_name_for_input(path):
                return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            logger.debug("location=%s" % location)
            ename = _get_exp_name_for_input(location)
            logger.debug("ename=%s" % ename)

            experiment_paramset = []
            self.load_metadata_builder(run_settings)
            if self.METADATA_BUILDER:
                experiment_paramset=self.METADATA_BUILDER.build_experiment_metadata(run_settings=run_settings)

            experiment_id = mytardis.create_experiment(
                settings=mytardis_settings,
                exp_id=experiment_id,
                expname=ename,
                experiment_paramset=experiment_paramset)
        else:
            logger.warn('Data curation is off')
        return experiment_id


    def create_dataset_for_input(self, experiment_id, run_settings, local_settings, output_storage_settings,
                    mytardis_settings, source_files_url):
        experiment_paramset=[]
        dataset_paramset=[]
        self.load_metadata_builder(run_settings)
        if self.METADATA_BUILDER:
            (experiment_paramset, dataset_paramset) = self.METADATA_BUILDER.build_metadata_for_input(
            source_files_url=source_files_url, run_settings=run_settings)

        output_prefix = '%s://%s@' % (output_storage_settings['scheme'],
                                    output_storage_settings['type'])
        output_host = output_storage_settings['host']

        def _get_dataset_name_for_input(settings, url, path):
            logger.debug("path=%s" % path)
            source_url = storage.get_url_with_credentials(
                output_storage_settings,
                output_prefix + os.path.join(output_host, path, self.VALUES_FNAME),
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
            exp_name=mytardis._get_exp_name_for_input,
            dataset_name=_get_dataset_name_for_input,
            experiment_paramset=experiment_paramset,
            dataset_paramset=dataset_paramset)
        return experiment_id

    def create_dataset_for_intermediate_output(self, run_settings, experiment_id, base_dir, output_url,
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
            output_dirs = []
            for m, dir_name in enumerate(node_output_dirnames):
                output_dirs.append(os.path.join(iter_output_dir, dir_name))

            for i, output_dir in enumerate(output_dirs):
                dataset_paramset = []
                datafile_paramset = []
                dfile_extract_func = {}
                self.load_metadata_builder(run_settings)
                if self.METADATA_BUILDER:
                    (continue_loop, dataset_paramset, datafile_paramset, dfile_extract_func) = \
                    self.METADATA_BUILDER.build_metadata_for_intermediate_output(\
                    output_dir, outputs, run_settings=run_settings, storage_settings=all_settings,\
                    output_dirs=output_dirs)
                    if continue_loop:
                        continue

                source_dir_url = get_url_with_credentials(
                    all_settings,
                    output_dir,
                    is_relative_path=False)
                logger.debug("source_dir_url=%s" % source_dir_url)
                logger.debug('all_settings_here=%s' % all_settings)
                system_id = int(getval(run_settings, '%s/system/id' % self.SCHEMA_PREFIX)) #TODO Mytardis

                experiment_id = mytardis.create_dataset(
                    settings=all_settings,
                    source_url=source_dir_url,
                    exp_id=experiment_id,
                    exp_name=mytardis.get_exp_name_for_intermediate_output,
                    dataset_name=mytardis.get_dataset_name_for_output,
                    dataset_paramset=dataset_paramset,
                    datafile_paramset=datafile_paramset,
                    dfile_extract_func=dfile_extract_func
                    )
        else:
            logger.warn("no mytardis host specified")
            return 0
        return experiment_id


    def create_dataset_for_final_output(self, run_settings, experiment_id, base_dir, output_url, all_settings):
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
                output_dirs = []
                for m, dir_name in enumerate(node_output_dirnames):
                    output_dirs.append(os.path.join(iter_output_dir, dir_name))

                for m, output_dir in enumerate(output_dirs):
                    #node_path = os.path.join(iter_output_dir, node_dir)
                    logger.debug("output_dir=%s" % output_dir)

                    dataset_paramset = []
                    datafile_paramset = []
                    dfile_extract_func = {}
                    self.load_metadata_builder(run_settings)
                    if self.METADATA_BUILDER:
                        (experiment_paramset, dataset_paramset, datafile_paramset, dfile_extract_func) = \
                        self.METADATA_BUILDER.build_metadata_for_final_output(output_dir, \
                        run_settings=run_settings, storage_settings=all_settings,\
                        output_dirs=output_dirs)

                    source_url = get_url_with_credentials(
                        all_settings, output_dir, is_relative_path=False)
                    logger.debug("source_url=%s" % source_url)

                    experiment_id = mytardis.create_dataset(
                        settings=all_settings,
                        source_url=source_url,
                        exp_name=mytardis.get_exp_name_for_output,
                        dataset_name=mytardis.get_dataset_name_for_output,
                        exp_id=experiment_id,
                        experiment_paramset=experiment_paramset,
                        dataset_paramset=dataset_paramset,
                        datafile_paramset=datafile_paramset,
                        dfile_extract_func=dfile_extract_func)
                    graph_paramset = []
            else:
                logger.warn("no mytardis host specified")
        else:
            logger.warn('Data curation is off')
        return experiment_id
