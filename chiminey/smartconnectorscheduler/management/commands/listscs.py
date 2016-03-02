__author__ = 'iman'

# Copyright (C) 2016, RMIT University

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


from django.core.management.base import BaseCommand
from django.conf import settings as django_settings
from pprint import pformat


class Command(BaseCommand):
    def list_scs(self, all=False):
        smart_connectors = django_settings.SMART_CONNECTORS
        if not all:
            print ("NAME:  DESCRIPTION")
            for k, v in smart_connectors.items():
                print ("%s:  %s" % (k,v['description']))
            return
        print(pformat(smart_connectors))

    def handle(self, *args, **options):
        list_all = False
        try:
            if args[0] in 'all':
                list_all = True
        except IndexError:
            pass
        finally:
             self.list_scs(all=list_all)