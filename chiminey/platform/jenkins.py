

import os
import logging

from chiminey import storage

from chiminey.platform.generatekeys import generate_unix_key
from chiminey.platform.validate import validate_remote_path
from chiminey.platform.manage import retrieve_platform

logger = logging.getLogger(__name__)


class JenkinsPlatform():

    def get_platform_types(self):
        return ['jenkins']

    def configure(self, platform_type, username, parameters):
        #def configure_unix_platform(platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        key_relative_path = os.path.join(
            '.ssh', username, platform_type, key_name)
        parameters['private_key_path'] = key_relative_path

    def validate(self, parameters, passwd_auth=False):
        path_list = [parameters['root_path'], parameters['home_path']]
        return validate_remote_path(path_list, parameters, passwd_auth)

    def generate_key(self, parameters):
        return generate_unix_key(parameters)

    def get_platform_settings(self, platform_url, username):
        platform_name = platform_url.split('/')[0]
        if platform_name == "local":
            return {"scheme": 'file', 'type': 'local', 'host': '127.0.0.1'}
        record, schema_namespace = retrieve_platform(platform_name, username)
        logger.debug("record=%s" % record)
        logger.debug("schema_namespace=%s" % schema_namespace)
        self._update_platform_settings(record)
        record['bdp_username'] = username
        return record

    def _update_platform_settings(self, settings):
        try:
            platform_type = settings['platform_type']
        except KeyError:
            logger.error("settings=%s" % settings)
            raise
        settings['type'] = platform_type
        settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                       settings['private_key_path'])
        settings['host'] = settings['ip_address']
        settings['scheme'] = 'ssh'
