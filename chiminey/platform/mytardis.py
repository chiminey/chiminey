
import os
import logging
from boto.exception import EC2ResponseError
from django.core.files.base import ContentFile

from chiminey import storage
from chiminey.sshconnection import open_connection, AuthError
from chiminey.compute import run_command_with_status
from chiminey.cloudconnection import \
    create_ssh_security_group, create_key_pair
from chiminey.platform.validate import validate_mytardis_parameters


logger = logging.getLogger(__name__)


class MyTardisPlatform():

    def get_platform_types(self):
        return ['mytardis']

    def configure(self, platform_type, username, parameters):
        #def configure_unix_platform(platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        key_relative_path = os.path.join(
            '.ssh', username, platform_type, key_name)
        parameters['private_key_path'] = key_relative_path

    def validate(self, parameters, passwd_auth=False):
        return validate_mytardis_parameters(parameters)

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

