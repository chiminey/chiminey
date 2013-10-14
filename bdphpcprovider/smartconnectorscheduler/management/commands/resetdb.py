from django.core.management.base import BaseCommand, CommandError
from bdphpcprovider.smartconnectorscheduler import mc

from bdphpcprovider.smartconnectorscheduler import models



class Command(BaseCommand):
    args = ''
    help = 'Deletes all non-super users and all associated contexts stages and schemas'

    def handle(self, *args, **options):

        confirm = raw_input("This will ERASE and reset the database.  Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return

        res = models.Schema.objects.all().delete()
        res = models.Context.objects.all().delete()
        res = models.Stage.objects.all().delete()
        res = models.Platform.objects.all().delete()
        res = models.User.objects.filter(is_superuser=False).delete()
        res = models.Directive.objects.all().delete()
        print "done"