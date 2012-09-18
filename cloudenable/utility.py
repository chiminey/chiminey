# contents of config.sys are ALWAYS read-only
def load_generic_settings(self):
        import ConfigParser
        config = ConfigParser.RawConfigParser()
        config_file = os.path.expanduser("~/.cloudenabling/config.sys")
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            config_file = os.path.expanduser("config.sys")  # a default config file
            if os.path.exists(config_file):
                config.read(config_file)
            else:
                logger.error("no configuration file found")
                sys.exit(1)
        
        environ_fields = ['USER_NAME', 'PASSWORD', 'PRIVATE_KEY',
                      'VM_SIZE',
                      'PAYLOAD_LOCAL_DIRNAME', 'PAYLOAD',
                      'DEST_PATH_PREFIX', 'DEPENDS', 'COMPILER',
                      'COMPILE_FILE', 'PAYLOAD_CLOUD_DIRNAME',
                      'SLEEP_TIME', 'RETRY_ATTEMPTS',
                      'OUTPUT_FILES', 'TEST_VM_IP',
                      'EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                      'CLOUD_SLEEP_INTERVAL', 'PRIVATE_KEY_NAME',
                      'SECURITY_GROUP', 'GROUP_ID_DIR', 'MAX_SEED_INT']

        import json
        settings = type('', (), {})()
        for field in environ_fields:
            #TODO: add multiple sections
            val = config.get("basic", field)
            if '#' in val:  # remove comments
                val, _ = val.split('#', 1)
            try:
                field_val = json.loads(val)    # use JSON to parse values
            except ValueError, e:
                file_val = ""
            # and make fake object to hold them
            setattr(settings, field, field_val)
            
            return settings