import logging
from django.core.validators import ValidationError
from bdphpcprovider.smartconnectorscheduler.platform import retrieve_platform


logger = logging.getLogger(__name__)

def validate_platform(value, username):
    value = value.strip()
    platform_name = value.split('/')[0]
    record, _ = retrieve_platform(platform_name, username)
    if not record:
        raise ValidationError('Platform [%s] is unknown' % platform_name)
    return value


