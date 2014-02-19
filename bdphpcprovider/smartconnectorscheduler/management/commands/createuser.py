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
import os
import getpass
import re
import sys
import shutil

from optparse import make_option
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from bdphpcprovider.smartconnectorscheduler import models


RE_VALID_USERNAME = re.compile('[\w.@+-]+$')

EMAIL_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain


copy_commands = (
    ("input2", "myfiles/input/initial"),
    ("vaspinput", "local/vaspinput/initial"),
    ("testinput", "local/testinput/initial"),
    ("payload2_new", "local/testpayload_new"),
    ("testpayload", "local/testpayload"),
    ("vasppayload", "local/vasppayload"),
    ("payload_randomnumber", "local/payload_randomnumber"),
    )

# mkdir /var/cloudenabling/remotesys/{$user}/myfiles
# mkdir /var/cloudenabling/remotesys/{$user}/myfiles/input
# cp -a /opt/cloudenabling/current/input2 /var/cloudenabling/remotesys/${user}/myfiles/input/initial
# cp -a /opt/cloudenabling/current/vaspinput /var/cloudenabling/remotesys/${user}/local/vaspinput/initial
# cp -a /opt/cloudenabling/current/payload2_new /var/cloudenabling/remotesys/${user}/local/testpayload_new
# cp -a /opt/cloudenabling/current/bdphpcprovider/randomnums.txt /var/cloudenabling/remotesys/{$user}
# cp -a /opt/cloudenabling/current/testpayload /var/cloudenabling/remotesys/{$user}/local/
# cp -a /opt/cloudenabling/current/vasppayload /var/cloudenabling/remotesys/${user}/local/


def is_valid_email(value):
    if not EMAIL_RE.search(value):
        raise exceptions.ValidationError(_('Enter a valid e-mail address.'))


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the user.'),
        make_option('--email', dest='email', default=None,
            help='Specifies the email address for the user.'),
        make_option('--remotefsys', dest='remotefsys',
            default="/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/testing/remotesys/",
            help='Specifies the email address for the user.'),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help=('Tells Django to NOT prompt the user for input of any kind. '
                  'You must use --username and --email with --noinput.')),
    )

    help = 'Used to create a BDPHPCProvider user.'

    def handle(self, *args, **options):
        username = options.get('username', None)
        email = options.get('email', None)
        interactive = options.get('interactive')
        remotefsys = options.get('remotefsys')
        verbosity = int(options.get('verbosity', 1))

        # Do quick and dirty validation if --noinput
        if not interactive:
            if not username or not email:
                raise CommandError("You must use --username and --email with --noinput.")
            if not RE_VALID_USERNAME.match(username):
                raise CommandError("Invalid username. Use only letters, digits, and underscores")
            try:
                is_valid_email(email)
            except exceptions.ValidationError:
                raise CommandError("Invalid email address.")

        # If not provided, create the user with an unusable password
        password = None

        # Try to determine the current system user's username to use as a default.
        try:
            default_username = getpass.getuser().replace(' ', '').lower()
        except (ImportError, KeyError):
            # KeyError will be raised by os.getpwuid() (called by getuser())
            # if there is no corresponding entry in the /etc/passwd file
            # (a very restricted chroot environment, for example).
            default_username = ''

        # Determine whether the default username is taken, so we don't display
        # it as an option.
        if default_username:
            try:
                User.objects.get(username=default_username)
            except User.DoesNotExist:
                pass
            else:
                default_username = ''

        # Prompt for username/email/password. Enclose this whole thing in a
        # try/except to trap for a keyboard interrupt and exit gracefully.
        if interactive:
            try:

                # Get a username
                while 1:
                    if not username:
                        input_msg = 'Username'
                        if default_username:
                            input_msg += ' (Leave blank to use %r)' % default_username
                        username = raw_input(input_msg + ': ')
                    if default_username and username == '':
                        username = default_username
                    if not RE_VALID_USERNAME.match(username):
                        sys.stderr.write("Error: That username is invalid. Use only letters, digits and underscores.\n")
                        username = None
                        continue
                    try:
                        User.objects.get(username=username)
                    except User.DoesNotExist:
                        break
                    else:
                        sys.stderr.write("Error: That username is already taken.\n")
                        username = None

                # Get an email
                while 1:
                    if not email:
                        email = raw_input('E-mail address: ')
                    try:
                        is_valid_email(email)
                    except exceptions.ValidationError:
                        sys.stderr.write("Error: That e-mail address is invalid.\n")
                        email = None
                    else:
                        break

                # Get a password
                while 1:
                    if not password:
                        password = getpass.getpass()
                        password2 = getpass.getpass('Password (again): ')
                        if password != password2:
                            sys.stderr.write("Error: Your passwords didn't match.\n")
                            password = None
                            continue
                    if password.strip() == '':
                        sys.stderr.write("Error: Blank passwords aren't allowed.\n")
                        password = None
                        continue
                    break
            except KeyboardInterrupt:
                sys.stderr.write("\nOperation cancelled.\n")
                sys.exit(1)

        standard_group = Group.objects.get(name="standarduser")

        user = User.objects.create_user(username, email, password)
        user.is_staff = True
        user.groups.add(standard_group)
        user.save()

        userProfile = models.UserProfile(user=user)
        userProfile.save()

        self.stdout.write("remotefsys=%s\n" % remotefsys)

        # Setup the schema for user configuration information (kept in profile)
        self.PARAMS = {
            # 'nci_user': 'iet595',
            # 'nci_password': 'changemepassword',  # NB: change this password
            # 'nci_host': 'raijin.nci.org.au',
            # 'nci_private_key': 'mynectarkey',
            # 'nectar_private_key': 'file://local@127.0.0.1/mynectarkey.pem',
            # 'nectar_private_key_name': '',
            # 'nectar_ec2_access_key': '',
            # 'nectar_ec2_secret_key': '',
            # 'mytardis_host': '',
            # 'mytardis_user': '',
            # 'mytardis_password': ''
            }

        #TODO: prompt user to enter private key paths and names and other credentials
        user_schema = models.Schema.objects.get(
            namespace=models.UserProfile.PROFILE_SCHEMA_NS)
        param_set, _ = models.UserProfileParameterSet.objects.get_or_create(
            user_profile=userProfile,
            schema=user_schema)
        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.get(schema=user_schema,
                name=k)
            models.UserProfileParameter.objects.get_or_create(name=param_name,
                paramset=param_set,
                value=v)
        try:
            os.makedirs(os.path.join(
                settings.LOCAL_FILESYS_ROOT_PATH,
                username))
            os.makedirs(os.path.join(
                settings.LOCAL_FILESYS_ROOT_PATH,
                username,
                "myfiles",
                "input"))
        except IOError, e:
            raise CommandError("cannot create user filesystem")
        except AttributeError, e:
            raise CommandError(
                "LOCAL_FILESYS_ROOT_PATH must be set in settings.py")

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        source_prefix = os.path.join(curr_dir, "..", "..", "..", "..")

        for src, dest in copy_commands:
            try:
                s = os.path.abspath(os.path.join(source_prefix, src))
                d = os.path.join(settings.LOCAL_FILESYS_ROOT_PATH, username, dest)
                self.stdout.write("%s -> %s" % (s, d))
                shutil.copytree(s, d)
            except IOError, e:
                raise CommandError("ERROR:%s\n" % e)

        shutil.copy(os.path.abspath(
            os.path.join(source_prefix, "bdphpcprovider", "randomnums.txt")),
            os.path.join(settings.LOCAL_FILESYS_ROOT_PATH, username))

        if verbosity >= 1:
            self.stdout.write("BDPHPCProvider user created successfully.\n")
