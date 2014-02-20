# Copyright (C) 2013, RMIT University

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
#
#
#

import json
import logging
from django.core.validators import ValidationError

from chiminey.platform.manage import retrieve_platform

logger = logging.getLogger(__name__)


def validate_platform(value, username):
    value = value.strip()
    platform_name = value.split('/')[0]
    record, _ = retrieve_platform(platform_name, username)
    if not record:
        raise ValidationError('Platform [%s] is unknown' % platform_name)
    return value


def validate_sweep_map(value):
    # FIXME: more detailed validation required here
    sweep_map = value
    try:
        json.loads(sweep_map)
    except Exception:
        msg = u'JSON is invalid'
        raise ValidationError(msg)
    return sweep_map


def validate_run_map(value):
    # FIXME: more detailed validation required here
    run_map = value
    try:
        json.loads(run_map)
    except Exception:
        msg = u'JSON is invalid'
        raise ValidationError(msg)
    return run_map


def validate_number_vm_instances(value):
    number_vm_instances = value
    msg = u'number of vm instances should be a positive integer'
    try:
        vms = int(number_vm_instances)
    except ValueError:
        raise ValidationError(msg)
    if vms <= 0:
        raise ValidationError(msg)

    return number_vm_instances


def validate_minimum_number_vm_instances(value):
    minimum_number_vm_instances = value
    msg = u'minimum number of vm instances should be a positive integer'
    try:
        vms = int(minimum_number_vm_instances)
    except ValueError:
        raise ValidationError(msg)
    if vms <= 0:
        raise ValidationError(msg)
    return minimum_number_vm_instances


def validate_fanout_per_kept_result(value):
    fanout_per_kept_result = value
    msg = u'No. fan out is an integer that is  greater than 0'
    try:
        nd = int(fanout_per_kept_result)
    except ValueError:
        raise ValidationError(msg)
    if nd < 1:
        raise ValidationError(msg)
    return fanout_per_kept_result


def validate_threshold(value):
    threshold = value
    msg = u'treshold should be "[X]" where X is number of vms to keep'
    try:
        thres = json.loads(threshold)
    except Exception:
        raise ValidationError(msg)
    if len(thres) == 1:
        try:
            th = int(thres[0])
        except IndexError:
            raise ValidationError(msg)
        except ValueError:
            raise ValidationError(msg)
        if th <= 0:
            raise ValidationError(msg)
        return threshold
    raise ValidationError(msg)


def validate_iseed(value):
    iseed = value
    msg = u'iseed should be a positive integer'
    try:
        vms = int(iseed)
    except ValueError:
        raise ValidationError(msg)
    if vms <= 0:
        raise ValidationError(msg)
    return iseed


def validate_pottype(value):
    pottype = value
    msg = u'pottype should be a 0 or 1'
    try:
        vms = int(pottype)
    except ValueError:
        raise ValidationError(msg)
    if not vms in [0, 1]:
        raise ValidationError(msg)
    return pottype


def validate_max_iteration(value):
    max_iteration = value
    msg = u'max_iteration should be a positive integer'
    try:
        vms = int(max_iteration)
    except ValueError:
        raise ValidationError(msg)
    if vms <= 0:
        raise ValidationError(msg)
    return max_iteration


def validate_error_threshold(value):
    error_threshold = value
    msg = u'error_threshold should be a positive real'
    try:
        vms = float(error_threshold)
    except ValueError:
        raise ValidationError(msg)
    if vms <= 0:
        raise ValidationError(msg)
    return error_threshold


def validate_experiment_id(value):
    experiment_id = value
    msg = u'experiment_id should be a positive integer'
    try:
        vms = int(experiment_id)
    except ValueError:
        raise ValidationError(msg)
    if vms < 0:
        raise ValidationError(msg)
    return experiment_id


def validate_hidden(value):
    return True


def validate_natural_number(value):
    # If the field is blank we assume zero
    if value is None or value == "":
        return 0
    msg = u'natural number'
    try:
        v = int(value)
    except ValueError:
        raise ValidationError(msg)
    if v < 0:
        raise ValidationError(msg)
    return value


def validate_whole_number(value):
    msg = u'whole number'
    logger.debug("checking whole number %s" % value)
    try:
        v = int(value)
    except ValueError:
        raise ValidationError(msg)
    if v < 1:
        raise ValidationError(msg)
    return value


def validate_float_number(value):
    msg = u'real number'
    try:
        float(value)
    except ValueError:
        raise ValidationError(msg)
    return value


def validate_even_number(value):
    msg = u'even number'
    try:
        v = int(value)
    except ValueError:
        raise ValidationError(msg)
    if not v % 2 == 0:
        raise ValidationError(msg)
    return value


def validate_string(value):
    return str(value)


def validate_string_not_empty(value):
    value = value.strip()
    if not len(str(value)):
        raise ValidationError('Empty')
    if ' ' in str(value):
        raise ValidationError('Space not allowed')
    return value


def validate_platform_url(value):
    value = value.strip()
    if not len(str(value)):
        raise ValidationError('BDP url is empty')
    if ' ' in str(value):
        raise ValidationError('Space in BDP url not allowed')
    platform_name = value.split('/')[0]
    if not platform_name:
        raise ValidationError('Platform name is missing from the BDP url')
    return value


def validate_BDP_url(value):
    logger.debug("checking bdpurl %s" % value)
    if not len(str(value)):
        raise ValidationError("BDP url is empty")
    return str(value)


def validate_bool(value):
    logger.debug("checking bool %s" % value)
    msg = u'boolean not valid'
    try:
        bool(value)
    except ValueError:
        raise ValidationError(msg)
    return int(value)


def validate_jsondict(value):
    logger.debug("checking jsondict")
    try:
        json.loads(value)
    except Exception:
        msg = u'JSON is invalid'
        raise ValidationError(msg)
    return str(value)


def check_addition(cleaned_data):
    arg1 = cleaned_data.get("http://rmit.edu.au/schemas/input2/arg1", 0)
    arg2 = cleaned_data.get("http://rmit.edu.au/schemas/input2/arg1", 0)
    arg3 = cleaned_data.get("http://rmit.edu.au/schemas/input2/arg3", 0)
    logger.debug("arg1=%s" % arg1)
    logger.debug("arg2=%s" % arg2)
    logger.debug("arg3=%s" % arg3)
    msg = u"arg3 must be arg1 + arg2"
    if arg1 + arg2 != arg3:
        raise ValidationError(msg)
    else:
        logger.debug("okay")


def myvalidate_choice_field(value, choices):
    msg = "Submitted value %s not found in choices %s" % (value, choices)
    logger.debug("checking %s for %s" % (value, choices))
    if value in choices:
        return value
    else:
        raise ValidationError(msg)
    return value
