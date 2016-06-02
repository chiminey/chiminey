

import os
import logging

from chiminey import storage
from chiminey.corestages import strategies
from chiminey.platform.generatekeys import generate_rfs_key
from chiminey.platform.validate import validate_remote_path
from chiminey.platform.manage import retrieve_platform
from chiminey.compute.command import run_command

logger = logging.getLogger(__name__)


class RemoteFileSystemPlatform():


    def get_platform_types(self):
        return ['rfs', 'nci']

    def configure(self, platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        key_relative_path = os.path.join(
            '.ssh', username, platform_type, key_name)
        parameters['private_key_path'] = key_relative_path
        try:
            parameters['port'] = int(parameters['port'])
        except ValueError:
            parameters['port'] = 22
        parameters['home_path'] = self.get_or_create_homepath(parameters)
        parameters['root_path'] = self.get_or_create_rootpath(parameters)


    def validate(self, parameters, passwd_auth=False):
        path_list = [parameters['home_path'], parameters['root_path']]
        return [True] + list(validate_remote_path(path_list, parameters, passwd_auth))

    def generate_key(self, parameters):
        return generate_rfs_key(parameters)

    # def get_platform_settings(self, platform_url, username):
    #     platform_name = platform_url.split('/')[0]
    #     if platform_name == "local":
    #         return {"scheme": 'file', 'type': 'local', 'host': '127.0.0.1'}
    #     record, schema_namespace = retrieve_platform(platform_name, username)
    #     logger.debug("record=%s" % record)
    #     logger.debug("schema_namespace=%s" % schema_namespace)
    #     self._update_platform_settings(record)
    #     record['bdp_username'] = username
    #     return record

    def get_or_create_homepath(self, parameters):
        home_path = parameters['home_path']
        if home_path:
            return home_path
        command = 'echo ~%s ||  echo $HOME ' % parameters['username']
        output, err = run_command(command, parameters['ip_address'], parameters)
        home_path = output[0].strip('\n')
        logger.debug('home_path=%s' % home_path)
        return home_path

    def get_or_create_rootpath(self, parameters):
        root_path = parameters['root_path']
        if not root_path:
            root_path = self.get_or_create_homepath(parameters)

        if parameters['class'] == 'compute' \
                and os.path.basename(root_path) != '.chimineywd':
            root_path = '%s/.chimineywd' % root_path
        run_command('mkdir -p %s' % root_path, parameters['ip_address'], parameters)
        logger.debug('root_path=%s' % parameters['root_path'])
        return root_path



    def update_platform_settings(self, settings):
        try:
            platform_type = settings['platform_type']
        except KeyError:
            logger.error("settings=%s" % settings)
            raise
        settings['type'] = platform_type
        if platform_type == 'nci':
            settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                           settings['private_key_path'])
            settings['host'] = settings['ip_address']
            settings['scheme'] = 'ssh'

        elif platform_type == 'rfs':
            settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                           settings['private_key_path'])
            settings['host'] = settings['ip_address']
            settings['scheme'] = 'ssh'

    def get_strategy(self, platform_type):
        #if platform_type == 'nci':
        return strategies.ClusterStrategy()
        #else:
        #    return None
