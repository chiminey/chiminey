from celery.task import task
import celery
from django.db import transaction
from django.db import DatabaseError
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages

import logging
import logging.config

logger = logging.getLogger(__name__)


@task(name="smartconnectorscheduler.test", ignore_result=True)
def test():
    print "Hello World"


@task(name="smartconnectorscheduler.run_contexts", ignore_result=True)
def run_contexts():
    try:
        for context in models.Context.objects.all():
            progress_context.delay(context.id)
    except Context.DoesNotExist, e:
        logger.warn("Context removed from other thread")


@task(name="smartconnectorscheduler.progress_context", ignore_result=True)
def progress_context(context_id):
    run_context = models.Context.objects.get(id=context_id)
    logger.debug("process context %s" % run_context)

    test_info = []
    with transaction.commit_on_success():
        try:
            run_context = models.Context.objects.select_for_update(nowait=True).get(id=run_context.id)
        except DatabaseError:
            logger.info("progress context for %s is already running.  exiting" % context_id)
            return
        else:
            logger.info("processing %s" % context_id)
        stage = run_context.current_stage
        logger.debug("stage=%s" % stage)
        children = models.Stage.objects.filter(parent=stage)
        if children:
            stageset = children
        else:
            siblings = models.Stage.objects.filter(parent=stage.parent)
            #stageset = siblings
            stageset = [stage]

        logger.debug("stageset=%s", stageset)
        profile = run_context.owner
        logger.debug("profile=%s" % profile)

        run_settings = run_context.get_context()
        logger.debug("retrieved run_settings=%s" % run_settings)

        user_settings = hrmcstages.retrieve_settings(profile)
        logger.debug("user_settings=%s" % user_settings)

        # FIXME: do we want to combine cont and user_settings to
        # pass into the stage?  The original code but the problem is separating them
        # again before they are serialised.

        triggered = 0
        for current_stage in stageset:
            # get the actual stage object
            stage = hrmcstages.safe_import(current_stage.package, [],
                {'user_settings': user_settings})  # obviously need to cache this
            logger.debug("process stage=%s", stage)

            if stage.triggered(run_settings):
                logger.debug("triggered")
                stage.process(run_settings)
                run_settings = stage.output(run_settings)
                logger.debug("updated run_settings=%s" % run_settings)
                run_context.update_run_settings(run_settings)
                logger.debug("run_settings=%s" % run_settings)
                triggered = True
            else:
                logger.debug("not triggered")

        if not triggered:
            logger.debug("none triggered")
            test_info = run_settings
            run_context.delete()

        logger.info("context task %s complete" % context_id)
        return test_info

def progress_context_old(context_id):

    run_context = models.Context.objects.get(id=context_id)

    with transaction.commit_on_success():
        logger.debug("run_context=%s" % run_context)
        run_context = models.Context.objects.select_for_update().get(id=run_context.id)

        current_stage = run_context.current_stage
        logger.debug("current_stage=%s" % current_stage)

        profile = run_context.owner
        logger.debug("profile=%s" % profile)

        run_settings = run_context.get_context()
        logger.debug("retrieved run_settings=%s" % run_settings)

        user_settings = hrmcstages.retrieve_settings(profile)
        logger.debug("user_settings=%s" % user_settings)

        # FIXME: do we want to combine cont and user_settings to
        # pass into the stage?  The original code but the problem is separating them
        # again before they are serialised.

        # get the actual stage object
        stage = hrmcstages.safe_import(current_stage.package, [],
            {'user_settings': user_settings})  # obviously need to cache this
        logger.debug("stage=%s", stage)

        if stage.triggered(run_settings):
            logger.debug("triggered")
            stage.process(run_settings)
            run_settings = stage.output(run_settings)
            logger.debug("updated run_settings=%s" % run_settings)
            run_context.update_run_settings(run_settings)
            logger.debug("run_settings=%s" % run_settings)
        else:
            logger.debug("not triggered")

        # advance to the next stage
        current_stage = run_context.current_stage.get_next_stage(run_settings)
        if not current_stage:
            #logger.debug("deleting")
            run_context.delete()
        else:
            # save away new stage to process
            run_context.current_stage = current_stage
            run_context.save()
