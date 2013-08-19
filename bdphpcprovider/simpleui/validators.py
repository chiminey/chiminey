import json
from django.core.validators import ValidationError

def validate_sweep_map(value):
    # FIXME: more detailed validation required here
    sweep_map = value
    try:
        map = json.loads(sweep_map)
    except Exception:
        msg = u'JSON is invalid'
        raise ValidationError(msg)
    return sweep_map


def validate_run_map(value):
    # FIXME: more detailed validation required here
    run_map = value
    try:
        map = json.loads(run_map)
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


def validate_number_dimensions(value):
    number_dimensions = value

    msg = u'number of dimensions should be in [1,2]'
    try:
        nd = int(number_dimensions)
    except ValueError:
        raise ValidationError(msg)
    if not nd in [1,2]:
        raise ValidationError(msg)
    return number_dimensions


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
    if not vms in [0,1]:
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


    # ['http://rmit.edu.au/schemas/hrmc',
    #     ('number_vm_instances', in [0,1],
    #     # TODO: in configure stage could copy this information from somewhere to this required location
    #     ('input_location',  'file://127.0.0.1/hrmcrun/input_0'),
    #     ('number_dimensions', 1),
    #     ('threshold', "[1]"),
    #     ('error_threshold', "0.03"),
    #     ('max_iteration', 20)



def validate_experiment_id(value):
    experiment_id = value

    msg = u'experiment_id should be a positive integer'
    try:
        vms = int(experiment_id)
    except ValueError:
        raise ValidationError(msg)

    if vms < 0 :
        raise ValidationError(msg)

    return experiment_id
