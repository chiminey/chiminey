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


import logging
from pprint import pformat


from bdphpcprovider.corestages.stage import (
    get_existing_key
)


logger = logging.getLogger(__name__)


def addMessage(run_settings, level, msg):
    try:
        context_id = get_existing_key(run_settings,
            "http://rmit.edu.au/schemas/system/contextid")
    except KeyError:
        logger.error("unable to load contextid from run_settings")
        logger.error(pformat(run_settings))
        return
    logger.debug("context_id=%s" % context_id)
    if not context_id:
        logger.error("invalid context_id")
        return
    mess = '%s,%s' % (level, msg)
    logger.debug("mess=%s" % mess)
    # Cannot write ContextMessage in same process as tasks.py
    # holds lock on all tables, so would get all messages
    # within a corestages at the end of the corestages process
    # With celery task, then some other worker (if available)
    # can do the task ASAP.
    # FIXME: this is circular import at global level
    from bdphpcprovider.smartconnectorscheduler import tasks

    tasks.context_message.delay(context_id, mess)


def debug(run_settings, msg):
    return addMessage(run_settings, 'debug', msg)


def info(run_settings, msg):
    return addMessage(run_settings, 'info', msg)


def success(run_settings, msg):
    return addMessage(run_settings, 'success', msg)


def warn(run_settings, msg):
    return addMessage(run_settings, 'warning', msg)


def error(run_settings, msg):
    return addMessage(run_settings, 'error', msg)
