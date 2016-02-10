# Copyright (C) 2014, RMIT University

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


import os
import logging

logger = logging.getLogger(__name__)



class RunsettingsException(Exception):
    """ A problem in the run_settings library"""
    pass

class SettingNotFoundException(KeyError):
    pass


class IncompatibleTypeException(RunsettingsException):
    pass



def _multilevel_key_exists(context, *parts):
    """
    Returns true if context contains all parts of the key, else
    false
    """
    c = dict(context)
    for p in parts:
        if p in c:
            c = c[p]
        else:
            #logger.warn("%s not found in context" % p)
            return False
    return True


def setval(context, key, value):
    """
    Sets the value of the key within the run settings context.

    :param context: current context
    :param key: the key to search
    :throws: runsettings.SettingNotFoundException if the schema part of key is not in the context.

    :throws: runsettings.IncompatibleTypeException  if the value is not compatible with the type of the key, according to the associated schema definition.

    """
    #TODO: Should check type of value to make sure it is conformant
    # to the required schema else raise IncompatibleTypeException
    try:
        context.setdefault(os.path.dirname(key),
                           {})[os.path.basename(key)] = value

    except KeyError:
        # Not clear that above an actually fail at all.
        pass


def setvals(context, key_vals):

    for k in key_vals.keys():
        setval(context, k, key_vals[k])


def getval(context, key):
    """
    Retrieves the current value of the key within the run setttings context.

    :param context: current context
    :param key: the key to search
    :raises: SettingNotFoundException if the schema part of the key is not in the context
    :return: the value for the key
    """
    res = None

    # logger.debug("context=%s" % context)
    if _multilevel_key_exists(context, os.path.dirname(key), os.path.basename(key)):
        # logger.debug("os.path.dirname(key) = %s" % os.path.dirname(key))
        # logger.debug("os.path.basename(key) = %s" % os.path.basename(key))
        res = context[os.path.dirname(key)][os.path.basename(key)]
    else:
        raise SettingNotFoundException("Cannot find %s in run_settings" % key)
    # logger.debug("getval %s == %s" % (key, repr(res)))

    return res


def getvals(context, base_key):
    if base_key in context:
        return context[base_key]
    else:
        raise SettingNotFoundException('Cannot find %s in run_settings' % base_key)


def delkey(context, key):
    k = getvals(context, os.path.dirname(key))
    del k[os.path.basename(key)]


def get_schema_namespaces(context):
    return context.keys()


def update(dest_dict, context, *keys):
    """
    """
    for k in keys:
        try:
            # Note that all run_settings and user_settings are flattened
            # logger.debug('context=%s' % context[os.path.dirname(k)])
            res = getval(context, k)
            # res = context[os.path.dirname(key)][os.path.basename(key)]
            dest_dict[os.path.basename(k)] = res
            # logger.debug("dest_contxt[%s] = %s" % (os.path.basename(k), repr(res)))
        except SettingNotFoundException:
            raise SettingNotFoundException("Error on key %s" % k)
