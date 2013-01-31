from django.core.management.base import BaseCommand, CommandError
from bdphpcprovider.smartconnectorscheduler import mc

class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        new_args = list(args)
        mc.start(new_args)
        print "done"