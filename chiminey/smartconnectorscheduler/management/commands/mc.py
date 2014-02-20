from django.core.management.base import BaseCommand, CommandError
from chiminey.smartconnectorscheduler import mc

class Command(BaseCommand):
    args = '<mc>'
    help = 'Runs the BDPHPCProvider'

    def handle(self, *args, **options):
        new_args = list(args)
        mc.start(new_args)
        print "done"