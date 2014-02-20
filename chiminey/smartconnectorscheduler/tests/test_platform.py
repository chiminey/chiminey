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

import unittest
from urlparse import urlparse

from django.contrib.auth.models import User, Group
from django.template.defaultfilters import slugify

from chiminey.smartconnectorscheduler import models
from chiminey.platform.manage \
    import create_platform_paramset, retrieve_platform_paramsets, delete_platform_paramsets,\
    update_platform_paramset, is_unique_platform_paramset, get_platform_and_schema,\
    filter_platform_paramsets, get_owner, all_params_present, required_param_exists


class TestPlatform(unittest.TestCase):
    def setUp(self):
        self.username = 'test_user'
        self.create_user(self.username)
        self.create_platform_schema()
        self.name = 'HRMC_tenancy'
        self.private_key = 'bdp'
        self.private_key_path = '/home/bdp/.ssh/bdp.pem'
        self.vm_image_size = 'm1.small'
        self.ec2_access_key = 'EC2_ACCESS_KEY_1234'
        self.ec2_secret_key = 'EC2_SECRET_KEY_5678'
        self.nectar_parameters =  {
            'name': self.name,
            'private_key': self.private_key,
            'private_key_path': self.private_key_path,
            'vm_image_size': self.vm_image_size,
            'ec2_access_key': self.ec2_access_key,
            'ec2_secret_key': self.ec2_secret_key
        }
        self.nci_parameters = {
            'private_key_path': '/short/h72',
            'username': 'user1'
        }
        self.nci_namespace = 'http://rmit.edu.au/schemas/platform/computation/test/nci'
        self.nectar_namespace = 'http://rmit.edu.au/schemas/platform/computation/test/nectar'
        self.unknown_namespace = 'http://rmit.edu.au/schemas/platform/computation/test/unknown'


    def create_user(self, username):
        standard_group = Group.objects.get(name="standarduser")
        user, _ = User.objects.get_or_create(username=username, email='iman@yahoo.com', password='12345')
        user.is_staff = True
        user.groups.add(standard_group)
        user.save()

        userProfile = models.UserProfile(user=user)
        userProfile.save()

        #print "remotefsys=%s" % remotefsys

        # Setup the schema for user configuration information (kept in profile)
        self.PARAMS = {
            'userinfo1': 'param1val',
            'userinfo2': 42,
            'nci_user': 'iet595',
            'nci_password': 'changemepassword',  # NB: change this password
            'nci_host': 'vayu.nci.org.au',
            'nci_private_key': 'mynectarkey',
            'nectar_private_key': 'file://local@127.0.0.1/mynectarkey.pem',
            'nectar_private_key_name': '',
            'nectar_ec2_access_key': '',
            'nectar_ec2_secret_key': '',
            'mytardis_host': '',
            'mytardis_user': '',
            'mytardis_password': ''
            }

        #TODO: prompt user to enter private key paths and names and other credentials

        user_schema = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)

        param_set, _ = models.UserProfileParameterSet.objects.get_or_create(user_profile=userProfile,
            schema=user_schema)

        for k, v in self.PARAMS.items():
            param_name = models.ParameterName.objects.get(schema=user_schema,
                name=k)
            models.UserProfileParameter.objects.get_or_create(name=param_name,
                paramset=param_set,
                value=v)


    def create_platform_schema(self):
        schema_data = {
            u'http://rmit.edu.au/schemas/platform/computation/test/nci':
                [u'schema for NeCTAR computation platform instances',
                 {
                     u'private_key_path': (models.ParameterName.STRING, '', 2),
                     u'username': (models.ParameterName.STRING, '', 1),
                     }
                ],
            u'http://rmit.edu.au/schemas/platform/computation/test/nectar':
                [u'schema for NeCTAR computation platform instances',
                 {
                     u'private_key_path': (models.ParameterName.STRING, '', 5),
                     u'vm_image_size': (models.ParameterName.STRING, '', 4),
                     u'ec2_secret_key': (models.ParameterName.STRING, '', 3),
                     u'ec2_access_key': (models.ParameterName.STRING, '', 2),
                     u'name': (models.ParameterName.STRING, '', 1),
                     }
                ],
            }
        for ns in schema_data:
            l = schema_data[ns]
            desc = l[0]
            kv = l[1:][0]
            url = urlparse(ns)

            context_schema, _ = models.Schema.objects.get_or_create(
                namespace=ns,
                defaults={'name': slugify(url.path.replace('/', ' ')),
                          'description': desc})

            for k, v in kv.items():
                val, help_text, ranking = (v[0], v[1], v[2])
                models.ParameterName.objects.get_or_create(
                    schema=context_schema,
                    name=k,
                    defaults={
                        'type': val, 'help_text': help_text,
                        'ranking': ranking})


    def tearDown(self):
        prefix = 'http://rmit.edu.au/schemas/platform/computation/test'
        platforms = models.PlatformInstance.objects.filter(
            schema_namespace_prefix__startswith=prefix)
        platforms.delete()
        schemas = models.Schema.objects.filter(
            namespace__startswith=prefix)
        schemas.delete()

        user = User.objects.get(username=self.username)
        user.delete()


    def test_create_platform_paramset(self):
        created = create_platform_paramset(self.username, self.nectar_namespace, self.nectar_parameters)
        self.assertTrue(created)

        created = create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.assertTrue(created)

        self.nectar_parameters['name'] = 'HRMC_Tenancy_II'
        filter_keys = ('name', 'unrecognized_field')
        created = create_platform_paramset(
            self.username, self.nectar_namespace,
            self.nectar_parameters, filter_keys=filter_keys)
        self.assertTrue(created)

        recreated = create_platform_paramset(
            self.username, self.nectar_namespace,
            self.nectar_parameters, filter_keys=filter_keys)
        self.assertFalse(recreated)

        self.nectar_parameters = {
            'name': 'HRMC_Tenancy_III',
            'private_key': self.private_key,
            'private_key': 'duplicate_key',
            'unrecognized_field': 'unrecognized',
            'private_key_path': self.private_key_path,
            'vm_image_size': self.vm_image_size,
            'ec2_access_key': self.ec2_access_key,
            'ec2_secret_key': self.ec2_secret_key
        }
        filter_keys = [k for k, v in self.nectar_parameters.items()]
        created = create_platform_paramset(
            self.username, self.nectar_namespace,
            self.nectar_parameters, filter_keys=filter_keys)
        self.assertTrue(created)

        created = create_platform_paramset(self.username, self.unknown_namespace, self.nectar_parameters)
        self.assertFalse(created)

        created = create_platform_paramset('unknown', self.nectar_namespace, self.nectar_parameters)
        self.assertFalse(created)


    def test_retrieve_platform_paramsets(self):
        create_platform_paramset(self.username, self.nectar_namespace, self.nectar_parameters)
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.nci_parameters['username'] = 'user2'
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'username': u'user2', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'name': u'HRMC_tenancy', u'vm_image_size': u'm1.small',
                     u'ec2_access_key': u'EC2_ACCESS_KEY_1234', u'private_key_path': u'/home/bdp/.ssh/bdp.pem',
                     u'ec2_secret_key': u'EC2_SECRET_KEY_5678', 'type': u'nectar'}]
        #fixme: upgrade to python 2.7, THEN replace self.assertEqual(sorted(expected), sorted(platform_records))
        #fixme by self.assertItemsEqual(expected, platform_records)
        self.assertEqual(sorted(expected), sorted(platform_records))
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'username': u'user2', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(expected), sorted(platform_records))
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nectar')
        expected = [{u'name': u'HRMC_tenancy', u'vm_image_size': u'm1.small',
                     u'ec2_access_key': u'EC2_ACCESS_KEY_1234', u'private_key_path': u'/home/bdp/.ssh/bdp.pem',
                     u'ec2_secret_key': u'EC2_SECRET_KEY_5678', 'type': u'nectar'}]
        self.assertEqual(sorted(platform_records), sorted(expected))


    def test_delete_platform_paramsets(self):
        create_platform_paramset(self.username, self.nectar_namespace, self.nectar_parameters)
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.nci_parameters['username'] = 'user2'
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        delete_platform_paramsets(self.username, self.nectar_namespace, {})
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'username': u'user2', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'name': u'HRMC_tenancy', u'vm_image_size': u'm1.small',
                     u'ec2_access_key': u'EC2_ACCESS_KEY_1234', u'private_key_path': u'/home/bdp/.ssh/bdp.pem',
                     u'ec2_secret_key': u'EC2_SECRET_KEY_5678', 'type': u'nectar'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        filter_field = {'username': 'user2'}
        delete_platform_paramsets(self.username, self.nci_namespace, filter_field)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'name': u'HRMC_tenancy', u'vm_image_size': u'm1.small',
                     u'ec2_access_key': u'EC2_ACCESS_KEY_1234', u'private_key_path': u'/home/bdp/.ssh/bdp.pem',
                     u'ec2_secret_key': u'EC2_SECRET_KEY_5678', 'type': u'nectar'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        filter_field = {'name': 'HRMC_tenancy', 'username': 'hrmc'}
        delete_platform_paramsets(self.username, self.nectar_namespace, filter_field)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nectar')
        expected = []
        self.assertEqual(sorted(platform_records), sorted(expected))


    def test_update_platform_paramsets(self):
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.nci_parameters['username'] = 'user2'
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'username': u'user2', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(platform_records), sorted(expected))

        new_parameters = dict(self.nci_parameters)
        new_parameters['username'] = 'user3'
        updated = update_platform_paramset(self.username, self.nci_namespace,
                                  self.nci_parameters, new_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user1', u'private_key_path': u'/short/h72', 'type': u'nci'},
                    {u'username': u'user3', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        self.assertTrue(updated)

        filter_field = {'username': 'user1'}
        new_parameters = dict(self.nci_parameters)
        new_parameters['username'] = 'user4'
        new_parameters['private_key_path'] = '/home/user4'
        updated = update_platform_paramset(self.username, self.nci_namespace,
                                  filter_field, new_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user4', u'private_key_path': u'/home/user4', 'type': u'nci'},
                    {u'username': u'user3', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        self.assertTrue(updated)

        filter_field = {'username': 'user3'}
        new_parameters = dict(self.nci_parameters)
        new_parameters['username'] = 'user4'
        new_parameters['private_key_path'] = '/home/user4'
        updated = update_platform_paramset(self.username, self.nci_namespace,
                                  filter_field, new_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user4', u'private_key_path': u'/home/user4', 'type': u'nci'},
                    {u'username': u'user3', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        self.assertFalse(updated)

        filter_field = {'username': 'unknown'}
        new_parameters['username'] = 'user5'
        updated = update_platform_paramset(self.username, self.nci_namespace,
                                  filter_field, new_parameters)
        platform_records = retrieve_platform_paramsets(
            self.username, 'http://rmit.edu.au/schemas/platform/computation/test/nci')
        expected = [{u'username': u'user4', u'private_key_path': u'/home/user4', 'type': u'nci'},
                    {u'username': u'user3', u'private_key_path': u'/short/h72', 'type': u'nci'}]
        self.assertEqual(sorted(platform_records), sorted(expected))
        self.assertFalse(updated)


    def test_is_unique_platform_paramset(self):
        filter_field = {'username': 'user1'}
        platform, schema = get_platform_and_schema(self.username, self.nci_namespace)
        unique = is_unique_platform_paramset(platform, schema, filter_field)
        self.assertTrue(unique)

        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        platform, schema = get_platform_and_schema(self.username, self.nci_namespace)
        unique = is_unique_platform_paramset(platform, schema, filter_field)
        self.assertFalse(unique)


    def test_filter_platform_paramsets(self):
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.nci_parameters['username'] = 'user2'
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        self.nci_parameters['username'] = 'user3'
        create_platform_paramset(self.username, self.nci_namespace, self.nci_parameters)
        filter_field = {'username': 'user1'}
        platform, schema = get_platform_and_schema(self.username, self.nci_namespace)
        filtered_platforms = filter_platform_paramsets(platform, schema, filter_field)
        self.assertEqual(1, len(filtered_platforms))
        filter_field = {'private_key_path': '/short/h72'}
        filtered_platforms = filter_platform_paramsets(platform, schema, filter_field)
        self.assertEqual(3, len(filtered_platforms))
        filter_field = {'private_key_path': '/new/path'}
        filtered_platforms = filter_platform_paramsets(platform, schema, filter_field)
        self.assertEqual(0, len(filtered_platforms))
        filter_field = {'unrecognized': '/short/h72'}
        filtered_platforms = filter_platform_paramsets(platform, schema, filter_field)
        self.assertEqual(0, len(filtered_platforms))
        platform, schema = get_platform_and_schema(self.username, self.nectar_namespace)
        filter_field = {'name': self.nectar_parameters['name']}
        filtered_platforms = filter_platform_paramsets(platform, schema, filter_field)
        self.assertEqual(0, len(filtered_platforms))


    def test_get_owner(self):
        owner = get_owner(self.username)
        self.assertEqual(owner.user.username, self.username)
        owner = get_owner('unknown')
        self.assertEqual(None, owner)


    def test_get_platform_and_schema(self):
        platform, schema = get_platform_and_schema(self.username, self.nci_namespace)
        self.assertEqual(platform, None)
        self.assertEqual(schema, None)

        owner = get_owner(self.username)
        models.PlatformInstance.objects.create(
            owner=owner, schema_namespace_prefix=self.nci_namespace)
        platform, schema = get_platform_and_schema(self.username, self.nci_namespace)
        self.assertEqual(platform.schema_namespace_prefix, self.nci_namespace)
        self.assertEqual(schema.namespace, self.nci_namespace)


    def test_all_platforms_present(self):
        schema = models.Schema.objects.get(namespace=self.nci_namespace)
        present, provided, required = all_params_present(schema, self.nci_parameters)
        self.assertTrue(present)
        self.assertEqual(provided, required)

        self.nci_parameters.popitem()
        present, provided, required = all_params_present(schema, self.nci_parameters)
        self.assertFalse(present)
        self.assertNotEqual(provided, required)


    def test_required_param_exists(self):
        schema = models.Schema.objects.get(namespace=self.nectar_namespace)
        exist = required_param_exists(schema, self.nectar_parameters)
        self.assertTrue(exist)

        self.nectar_parameters.popitem()
        exist = required_param_exists(schema, self.nectar_parameters)
        self.assertTrue(exist)

        self.nectar_parameters = {'username': 'nectar_user'}
        exist = required_param_exists(schema, self.nectar_parameters)
        self.assertFalse(exist)