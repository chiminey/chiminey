

import os
import logging
import requests


from chiminey import storage
from chiminey.corestages import strategies
from chiminey.platform.generatekeys import generate_unix_key
from chiminey.platform.validate import validate_remote_path
from chiminey.platform.manage import retrieve_platform

logger = logging.getLogger(__name__)


class JenkinsPlatform():

    def get_platform_types(self):
        return ['jenkins']

    def configure(self, platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        # key_relative_path = os.path.join(
        #     '.ssh', username, platform_type, key_name)
        # parameters['private_key_path'] = key_relative_path

    def validate(self, parameters, passwd_auth=False):

        JOB_LOG_URL = "http://%s:8080/api/json"

        username = parameters['username']
        password = parameters['password']

        url = JOB_LOG_URL  % parameters['ip_address']
        logger.info("url=%s" % url)
        response = requests.get(url, auth=(username, password), verify=False)
        logger.info("response code=%s" % response.status_code)

        if response.status_code != 200:
            return [True, False, 'Cannot register this jenkins instance']

        return [True, True, "Valid Jenkins instance found"]
        #
        # path_list = [parameters['root_path'], parameters['home_path']]
        # val = validate_remote_path(path_list, parameters, passwd_auth)
        # return [False] + list(val)

    def generate_key(self, parameters):
        return (True, "")
        # TODO: connect to jenkins to make sure valid host
        # return generate_unix_key(parameters)

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

    def update_platform_settings(self, settings):
        try:
            platform_type = settings['platform_type']
        except KeyError:
            logger.error("settings=%s" % settings)
            raise
        settings['type'] = platform_type
        # settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
        #                settings['private_key_path'])
        #
        settings['host'] = settings['ip_address']
        settings['scheme'] = 'ssh'


    def get_strategy(self, platform_type):
        # TODO: have an null strategy for platforms that don't have this attribute
        return strategies.JenkinsStrategy()
