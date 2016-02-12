import os
import logging

from chiminey.platform.generatekeys import generate_cloud_key
from chiminey import storage
from chiminey.corestages import strategies


logger = logging.getLogger(__name__)

class CloudPlatform():

    def get_platform_types(self):
        return ['csrack', 'nectar', 'amazon']

    def configure(self, platform_type, username, parameters):
        #def configure_nectar_platform(platform_type, username, parameters):
        key_name = 'bdp_%s' % parameters['platform_name']
        key_relative_path = '%s.pem' % os.path.join(
            '.ssh', username, platform_type, key_name)
        parameters['private_key'] = key_name
        parameters['private_key_path'] = key_relative_path
        parameters['security_group'] = 'bdp_ssh_group'
        if not parameters['vm_image_size']:
            parameters['vm_image_size'] = 'm1.small'

    def validate(self, parameters, passwd_auth=False):
        return [True, True, "All valid parameters"]

    def generate_key(self, parameters):
        return generate_cloud_key(parameters)

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

    def update_platform_settings(self, settings):
        try:
            platform_type = settings['platform_type']
        except KeyError:
            logger.error("settings=%s" % settings)
            raise
        settings['type'] = platform_type

        if platform_type in ['csrack', 'amazon']:
            #settings['username'] = 'root' #fixme avoid hardcoding
            settings['username'] = 'centos' #fixme avoid hardcoding
            settings['private_key_name'] = settings['private_key']
            settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                                   settings['private_key_path'])
            settings['root_path'] = '/home/centos'  # fixme avoid hardcoding
            settings['scheme'] = 'ssh'

        elif platform_type in ['nectar']:
            settings['username'] = 'ec2-user' #fixme avoid hardcoding
            settings['private_key_name'] = settings['private_key']
            settings['private_key'] = os.path.join(storage.get_bdp_root_path(),
                                                   settings['private_key_path'])
            settings['root_path'] = '/home/ec2-user'  # fixme avoid hardcoding
            settings['scheme'] = 'ssh'

    def get_strategy(self, platform_type):
        return strategies.CloudStrategy()
