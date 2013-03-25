from django.core.management.base import BaseCommand, CommandError
from bdphpcprovider.smartconnectorscheduler import ndim
from bdphpcprovider.smartconnectorscheduler import tasks

from bdphpcprovider.smartconnectorscheduler.tasks import run_contexts

class Command(BaseCommand):
    args = ''
    help = 'Fires one run_contexts task (for debugging without celerybeat'

    def handle(self, *args, **options):
        run_contexts.apply_async(args=[])
        print "done"
