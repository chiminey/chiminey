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

import sys
import linecache
import logging
from celery.task import task
from celery.exceptions import SoftTimeLimitExceeded
from pprint import pformat

from django.db import transaction
from django.db import DatabaseError
from django.core.exceptions import ImproperlyConfigured
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages

from bdphpcprovider import messages

import redis

from copy import deepcopy

# for celery 3.0
# from celery.utils.log import get_task_logger
# logger = get_task_logger(__name__)

logger = logging.getLogger(__name__)


CELERY_TIMEOUT = 50000
REDIS_TIMEOUT = 50000


@task(name="smartconnectorscheduler.test", ignore_result=True)
def test():
    print "Hello World"


@task(name="smartconnectorscheduler.delete", time_limit=CELERY_TIMEOUT, ignore_result=True)
def delete(context_id):
    try:
        try:
            run_context = models.Context.objects.get(id=context_id, deleted=False)
        except models.Context.DoesNotExist:
            logger.warn("Context %s removed from other thread" % context_id)
            return
        logger.debug("delete context %s" % run_context)

        with transaction.commit_on_success():
            try:
                run_context = models.Context.objects.select_for_update().get(
                    id=run_context.id, deleted=False)
            except DatabaseError:
                logger.info("progress context for %s is already deleted.  exiting"
                    % context_id)
                return
            except models.Context.DoesNotExist:
                logger.info("progress context for %s is already deleted.  exiting"
                    % context_id)
            else:
                logger.info("deleting %s" % context_id)
            run_context.deleted = True
            run_context.save()
    except SoftTimeLimitExceeded:
        raise


@task(name="smartconnectorscheduler.run_contexts", time_limit=CELERY_TIMEOUT, ignore_result=True)
def run_contexts():
    # Collect all valid contexts and process all         getting new set. This
    # should ensure that difficult for one user to monopolise processor, though
    # still not effective against DoS attack of job submission requests...
    logger.debug("run_contexts")
    try:
        for context in models.Context.objects.filter(deleted=False):
            # logger.debug("checking context=%s" % context)
            progress_context.delay(context.id)
    except models.Context.DoesNotExist:
        logger.warn("Context removed from other thread")
    except SoftTimeLimitExceeded:
        raise


@task(name="smartconnectorscheduler.context_message", time_limit=CELERY_TIMEOUT, ignore_result=True)
def context_message(context_id, mess):
    """ Add a message to context_id """
    logger.debug("trying to create message %s for context %s" % (mess, context_id))
    try:
        with transaction.commit_on_success():
            try:
                messages = models.ContextMessage.objects.select_for_update().filter(context__id=context_id)
            except DatabaseError:
                logger.info("context_message for %s is already running.  exiting"
                    % context_id)
                return
            except Exception, e:
                logger.error(e)
                return

            if not len(messages):
                message = models.ContextMessage()
                logger.debug("creating new message for %s" % context_id)
            else:
                message = messages[0]

            message.message = mess

            try:
                context = models.Context.objects.get(id=context_id)
            except models.Context.DoesNotExist:
                logger.error("cannot retrieve context %s" % context_id)
                return
            message.context = context
            message.save()
    except SoftTimeLimitExceeded:
        raise

# import redis

# REDIS_CLIENT = redis.Redis()


# def only_one(function=None, key="", timeout=None):
#     """Enforce only one celery task at a time."""

#     def _dec(run_func):
#         """Decorator."""

#         def _caller(*args, **kwargs):
#             """Caller."""
#             ret_value = None
#             have_lock = False
#             lock = REDIS_CLIENT.lock(key, timeout=timeout)
#             try:
#                 have_lock = lock.acquire(blocking=False)
#                 if have_lock:
#                     ret_value = run_func(*args, **kwargs)
#             finally:
#                 if have_lock:
#                     lock.release()

#             return ret_value

#         return _caller

#     return _dec(function) if function is not None else _dec


# class SingleTask(Task):
#     """A task."""

#     @only_one(key="SingleTask", timeout=60 * 5)
#     def run(self, **kwargs):
#         """Run task."""
#         print("Acquired lock for up to 5 minutes and ran task!")


def _process_context(context_id):
    test_info = []
    with transaction.commit_on_success():
        logger.debug("progress_context.context_id=%s" % context_id)
        try:
            run_context = models.Context.objects.select_for_update(
                nowait=True).get(id=context_id, deleted=False)
        except DatabaseError:
            logger.debug("progress context for %s is already running.  exiting"
                % context_id)
            return
        except models.Context.DoesNotExist, e:
            logger.debug("Context %s removed from other thread" % context_id)
            return
        except Exception, e:
            logger.error(e)
            return
        else:
            logger.info("Processing %s" % context_id)

        run_context = models.Context.objects.get(id=context_id, deleted=False)
        logger.debug("Executing task id %r, args: %r kwargs: %r" % (progress_context.request.id, progress_context.request.args, progress_context.request.kwargs))
        stage = run_context.current_stage
        logger.debug("stage=%s" % stage)
        children = models.Stage.objects.filter(parent=stage)
        if children:
            stageset = children
        else:
            #siblings = models.Stage.objects.filter(parent=stage.parent)
            #stageset = siblings
            stageset = [stage]

        logger.debug("stageset=%s", stageset)
        profile = run_context.owner
        logger.debug("profile=%s" % profile)

        run_settings = run_context.get_context()
        logger.debug("retrieved run_settings=%s" % pformat(run_settings))

        # user_settings are r/w during execution, but original values
        # associated with UserProfile are unchanged as loaded once on
        # context creation.
        #user_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
        # PROFILE_SCHEMA is now deprecated, so
        user_settings = {}

        triggered = 0
        for current_stage in stageset:

            logger.debug("checking stage %s for trigger" % current_stage.name)
            # get the actual stage object
            try:
                stage = hrmcstages.safe_import(current_stage.package, [],
                {'user_settings': deepcopy(user_settings)})  # obviously need to cache this
            except ImproperlyConfigured, e:
                logger.error(e)
                messages.error(run_settings, "0: internal error (%s stage):%s" % (str(current_stage.name), e))
                raise

            logger.debug("process stage=%s", stage)

            task_run_settings = deepcopy(run_settings)
            logger.debug("starting task settings = %s" % pformat(task_run_settings))
            # stage_settings are read only as transfered into context here
            stage_settings = current_stage.get_settings()
            logger.debug("stage_settings=%s" % stage_settings)

            # This is nasty
            task_run_settings = hrmcstages.transfer(task_run_settings, stage_settings)
            #task_run_settings.update(stage_settings)
            logger.debug("task run_settings=%s" % task_run_settings)

            logger.debug("Stage '%s' testing for triggering" % current_stage.name)
            try:
                if stage.is_triggered(deepcopy(task_run_settings)):
                    logger.debug("Stage '%s' TRIGGERED" % current_stage.name)
                    stage.process(deepcopy(task_run_settings))
                    task_run_settings = stage.output(task_run_settings)
                    logger.debug("updated task_run_settings=%s" % pformat(task_run_settings))
                    run_context.update_run_settings(task_run_settings)
                    logger.debug("task_run_settings=%s" % pformat(task_run_settings))
                    logger.debug("context run_settings=%s" % pformat(run_context))

                    triggered = True
                    break
                else:
                    logger.debug("Stage '%s' NOT TRIGGERED" % current_stage.name)
            except Exception, e:
                # exc_type, exc_obj, tb = sys.exc_info()
                # while tb.tb_next:
                #     tb = tb.tb_next
                # f = tb.tb_frame
                # lineno = tb.tb_lineno
                # filename = f.f_code.co_filename
                # linecache.checkcache(filename)
                # line = linecache.getline(filename, lineno, f.f_globals)
                # file_info = 'EXCEPTION IN (%s LINE %s "%s"): %s' % (filename, lineno, line.strip(), exc_obj)
                file_info = ""
                logger.error("0: internal error (%s stage):%s %s" % (str(current_stage.name), e, file_info))
                messages.error(run_settings, "0: internal error (%s stage):%s %s" % (str(current_stage.name), e, file_info))
        if not triggered:
            logger.debug("No corestages is_triggered")
            test_info = task_run_settings
            run_context.deleted = True
            run_context.save()
            #run_context.delete()

        logger.info("processing of context task %s complete" % (context_id))


@task(name="smartconnectorscheduler.progress_context", time_limit=CELERY_TIMEOUT, ignore_result=True)
def progress_context(context_id):
    # http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
    try:
        have_lock = False
        my_lock = redis.Redis().lock(str(context_id), timeout=REDIS_TIMEOUT)
        try:
            have_lock = my_lock.acquire(blocking=False)
            if have_lock:
                logger.debug("Got lock for %s" % context_id)
                _process_context(context_id)
            else:
                logger.debug("Did not acquire lock for %s" % context_id)
                return
        finally:
            if have_lock:
                logger.debug("releasing lock for %s" % context_id)
                my_lock.release()
            else:
                logger.debug("don't have lock for %s" % context_id)

    except SoftTimeLimitExceeded:
        raise
    except Exception, e:
        # FIXME: is there is unrecoverable error, task must give up lock
        logger.error('tasks.py %s=%s' % (context_id, e))
        raise


# FIXME: The following blocks using db locks, but still has a race condition, so
# use approach above using redis.
#@task(name="smartconnectorscheduler.progress_context", time_limit=CELERY_TIMEOUT, ignore_result=True)
def progress_context_broken(context_id):
    try:
        try:
            # try:
            #     run_context = models.Context.objects.get(id=context_id, deleted=False)
            # except models.Context.DoesNotExist:
            #     logger.warn("Context %s removed from other thread" % context_id)
            #     return
            # logger.debug("try to process context %s" % run_context)

            test_info = []
            with transaction.commit_on_success():
                logger.debug("progress_context.context_id=%s" % context_id)
                try:
                    run_contexts = models.Context.objects.select_for_update(
                        nowait=True).filter(id=context_id, deleted=False)
                    r_cont = run_contexts[0]
                except DatabaseError:
                    logger.debug("progress context for %s is already running.  exiting"
                        % context_id)
                    return
                except models.Context.DoesNotExist, e:
                    logger.debug("Context %s removed from other thread" % context_id)
                    return
                except Exception, e:
                    logger.error("uknown error")
                    logger.error(e)
                    return
                else:
                    logger.info("Processing %s" % context_id)

                logger.debug("r_cont=%s" % r_cont)
                run_context = models.Context.objects.get(id=context_id, deleted=False)
                logger.debug("Executing task id %r, args: %r kwargs: %r" % (progress_context.request.id, progress_context.request.args, progress_context.request.kwargs))
                stage = run_context.current_stage
                logger.debug("stage=%s" % stage)
                children = models.Stage.objects.filter(parent=stage)
                if children:
                    stageset = children
                else:
                    #siblings = models.Stage.objects.filter(parent=stage.parent)
                    #stageset = siblings
                    stageset = [stage]

                logger.debug("stageset=%s", stageset)
                profile = run_context.owner
                logger.debug("profile=%s" % profile)

                run_settings = run_context.get_context()
                logger.debug("retrieved run_settings=%s" % pformat(run_settings))

                # user_settings are r/w during execution, but original values
                # associated with UserProfile are unchanged as loaded once on
                # context creation.
                #user_settings = run_settings[models.UserProfile.PROFILE_SCHEMA_NS]
                # PROFILE_SCHEMA is now deprecated, so
                user_settings = {}

                triggered = 0
                for current_stage in stageset:

                    # get the actual stage object
                    stage = hrmcstages.safe_import(current_stage.package, [],
                        {'user_settings': deepcopy(user_settings)})  # obviously need to cache this
                    logger.debug("process stage=%s", stage)

                    task_run_settings = deepcopy(run_settings)
                    logger.debug("starting task settings = %s" % pformat(task_run_settings))
                    # stage_settings are read only as transfered into context here
                    stage_settings = current_stage.get_settings()
                    logger.debug("stage_settings=%s" % stage_settings)

                    # This is nasty
                    task_run_settings = hrmcstages.transfer(task_run_settings, stage_settings)
                    #task_run_settings.update(stage_settings)
                    logger.debug("task run_settings=%s" % task_run_settings)

                    logger.debug("Stage '%s' testing for triggering" % current_stage.name)
                    try:
                        if stage.is_triggered(deepcopy(task_run_settings)):
                            logger.debug("Stage '%s' TRIGGERED" % current_stage.name)
                            stage.process(deepcopy(task_run_settings))
                            task_run_settings = stage.output(task_run_settings)
                            logger.debug("updated task_run_settings=%s" % pformat(task_run_settings))
                            run_context.update_run_settings(task_run_settings)
                            logger.debug("task_run_settings=%s" % pformat(task_run_settings))
                            logger.debug("context run_settings=%s" % pformat(run_context))

                            triggered = True
                            break
                        else:
                            logger.debug("Stage '%s' NOT TRIGGERED" % current_stage.name)
                    except Exception, e:
                        messages.error(run_settings, "0: internal error:%s" % e)
                if not triggered:
                    logger.debug("No corestages is_triggered")
                    test_info = task_run_settings
                    run_context.deleted = True
                    run_context.save()
                    #run_context.delete()

                logger.info("processing of context task %s complete" % (context_id))
        except SoftTimeLimitExceeded:
            raise
    except Exception, e:
        logger.debug('tasks.py=%s' % e)
        raise


