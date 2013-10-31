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
import tempfile
import logging
import logging.config
import json
from pprint import pformat
from tastypie.test import ResourceTestCase
from tastypie.models import ApiKey

from flexmock import flexmock
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.db.models import Q

from urlparse import urlparse
from django.template.defaultfilters import slugify

from bdphpcprovider.smartconnectorscheduler.management.commands import view
from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.stages.errors import BadInputException

logger = logging.getLogger(__name__)

def error(e):
    raise


class UserResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(UserResourceTest, self).setUp()

        # Create a user.
        self.username = 'daniel'
        self.api_key = 'pass'
        self.password = 'pass'

        self.user = User.objects.create_user(self.username,
            'daniel@example.com', self.password)

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

        # FIXME: returns 401, followed by 200, so ValidJSONReponse fails.
        # def get_credentials(self):
        #         return self.create_digest(username=self.username,
        #             api_key=self.api_key, method="API", uri="foo")

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/user/', format='json',
            authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        # Here, we're checking an entire structure for the expected data.
        res = self.deserialize(resp)['objects'][0]
        self.assertEquals(res['id'], self.user.pk)
        self.assertEquals(res['username'], self.username)
        self.assertEquals(res['resource_uri'],
            '/api/v1/user/{0}/'.format(self.user.pk))



class UserProfileResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(UserProfileResourceTest, self).setUp()

        # Create a user.
        self.username = 'daniel'
        self.api_key = 'pass'
        self.password = 'pass'
        self.company = 'here'

        self.user = User.objects.create_user(self.username,
            'daniel@example.com', self.password)
        self.user_profile = models.UserProfile(user=self.user,
            company=self.company, nickname="danny")
        self.user_profile.save()
        apikey = ApiKey.objects.get(user=self.user)
        self.api_key = apikey.key
        logger.debug("api_key=%s"  % self.api_key)
        self.pk = self.user_profile.pk

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    # def get_credentials(self):
    #     return self.create_digest(username=self.username,
    #         api_key=self.api_key, method="MD5", uri='/api/v1/userprofile/%s/' % self.pk)

    def test_get_list_json(self):
        cred = self.get_credentials()
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get('/api/v1/userprofile/', format='json',
            authentication=cred)
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        # Here, we're checking an entire structure for the expected data.
        res = self.deserialize(resp)['objects'][0]
        logger.debug("res=%s" % res)
        self.assertEquals(res['id'], self.user.pk)
        self.assertEquals(res['company'], self.company)
        self.assertEquals(res['resource_uri'],
            '/api/v1/userprofile/{0}/'.format(self.user.pk))

    def test_bad_credentials_json(self):
        cred = self.create_basic(username=self.username, password="badpasswd")
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get('/api/v1/userprofile/', format='json',
            authentication=cred)
        self.assertHttpUnauthorized(resp)



class SchemaResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(SchemaResourceTest, self).setUp()


        self.namespace1 = 'http://rmit.edu.au/schemas/foo'
        self.name1 = 'Foo'
        self.namespace2 = 'http://rmit.edu.au/schemas/bar'
        self.name2 = 'Bar'

        self.schema1 = models.Schema(namespace=self.namespace1,
            name=self.name1)
        self.schema1.save()

        self.schema2 = models.Schema(namespace=self.namespace2,
            name=self.name2)
        self.schema2.save()

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/schema/', format='json')
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        # Here, we're checking an entire structure for the expected data.
        res = self.deserialize(resp)['objects'][0]
        logger.debug("res=%s" % res)
        self.assertEquals(res['id'], self.schema1.pk)
        self.assertEquals(res['namespace'], self.namespace1)
        self.assertEquals(res['name'], self.name1)
        self.assertEquals(res['resource_uri'],
            '/api/v1/schema/{0}/'.format(self.schema1.pk))

        res = self.deserialize(resp)['objects'][1]
        logger.debug("res=%s" % res)
        self.assertEquals(res['id'], self.schema2.pk)
        self.assertEquals(res['namespace'], self.namespace2)
        self.assertEquals(res['name'], self.name2)
        self.assertEquals(res['resource_uri'],
            '/api/v1/schema/{0}/'.format(self.schema2.pk))



class ParameterNameResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(ParameterNameResourceTest, self).setUp()

        self.namespace1 = 'http://rmit.edu.au/schemas/foo'
        self.name1 = 'Foo'

        self.schema = models.Schema(namespace=self.namespace1,
            name=self.name1)
        self.schema.save()


        self.paramname = 'Baz'
        self.paramtype = models.ParameterName.STRING

        self.param = models.ParameterName(name=self.paramname,
            type=self.paramtype, schema=self.schema)
        self.param.save()

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/parametername/', format='json')
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        # Here, we're checking an entire structure for the expected data.
        res = self.deserialize(resp)['objects'][0]
        logger.debug("res=%s" % res)
        self.assertEquals(res['id'], self.param.pk)
        self.assertEquals(res['name'], self.paramname)
        self.assertEquals(res['type'], self.paramtype)
        self.assertEquals(res['resource_uri'],
            '/api/v1/parametername/{0}/'.format(self.param.pk))
        self.assertEquals(res['schema'],
            '/api/v1/schema/{0}/'.format(self.schema.pk))


class UserProfileResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(UserProfileResourceTest, self).setUp()

        # Create a user.
        self.username = 'daniel'
        self.api_key = 'pass'
        self.password = 'pass'
        self.company = 'here'

        self.user = User.objects.create_user(self.username,
            'daniel@example.com', self.password)
        self.user_profile = models.UserProfile(user=self.user,
            company=self.company, nickname="danny")
        self.user_profile.save()

        self.namespace1 = 'http://rmit.edu.au/schemas/foo'
        self.name1 = 'Foo'

        self.schema = models.Schema(namespace=self.namespace1,
            name=self.name1)
        self.schema.save()

        self.paramset = models.UserProfileParameterSet(user_profile=self.user_profile,
            schema=self.schema)
        self.paramset.save()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    # def get_credentials(self):
    #     return self.create_digest(username=self.username,
    #         api_key=self.api_key, method="MD5", uri='/api/v1/userprofile/%s/' % self.pk)

    def test_get_list_json(self):
        cred = self.get_credentials()
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get('/api/v1/userprofileparameterset/', format='json',
            authentication=cred)
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        # Here, we're checking an entire structure for the expected data.
        res = self.deserialize(resp)['objects'][0]
        logger.debug("res=%s" % res)
        self.assertEquals(res['id'], self.user.pk)
        self.assertEquals(res['schema'],
            '/api/v1/schema/{0}/'.format(self.schema.pk))
        self.assertEquals(res['user_profile'],
            '/api/v1/userprofile/{0}/'.format(self.user_profile.pk))
        self.assertEquals(res['resource_uri'],
            '/api/v1/userprofileparameterset/{0}/'.format(self.paramset.pk))

    def test_bad_credentials_json(self):
        cred = self.create_basic(username=self.username, password="badpasswd")
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get('/api/v1/userprofileparameterset/', format='json',
            authentication=cred)
        self.assertHttpUnauthorized(resp)


class ContextResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(ContextResourceTest, self).setUp()

        # Create a user.
        self.username = 'daniel'
        self.api_key = 'pass'
        self.password = 'pass'
        self.company = 'here'

        self.user = User.objects.create_user(self.username,
            'daniel@example.com', self.password)
        self.user_profile = models.UserProfile(user=self.user,
            company=self.company, nickname="danny")
        self.user_profile.save()



        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(
                codename="change_%s" % model_name)
            self.group.permissions.add(change_model)

        standard_group = Group.objects.get(name="standarduser")

        self.user.is_staff = True
        self.user.groups.add(standard_group)
        self.user.save()

        self.namespace1 = 'http://rmit.edu.au/schemas/foo'
        self.name1 = 'Foo'

        self.schema = models.Schema(namespace=self.namespace1,
            name=self.name1)
        self.schema.save()

        self.paramset = models.UserProfileParameterSet(user_profile=self.user_profile,
            schema=self.schema)
        self.paramset.save()

        self.paramname = 'Baz'
        self.paramtype = models.ParameterName.NUMERIC

        self.param = models.ParameterName(name=self.paramname,
            type=self.paramtype, schema=self.schema)
        self.param.save()

        self.userparam = models.UserProfileParameter(name=self.param,
            paramset=self.paramset, value='42')
        self.userparam.save()

        self.detail_url = '/api/v1/userprofileparameter/{0}/?format=json'.format(self.userparam.pk)


    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    # def get_credentials(self):
    #     return self.create_digest(username=self.username,
    #         api_key=self.api_key, method="MD5", uri='/api/v1/userprofile/%s/' % self.pk)

    def test_put_detail(self):
        # Grab the current data & modify it slightly.
        logger.debug("detail_url=%s" % self.detail_url)
        original_data = self.deserialize(self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials()))
        new_data = original_data.copy()
        logger.debug("new_data=%s" % new_data)
        data = {}
        data[u'value'] = '43'

        self.assertEqual(models.UserProfileParameter.objects.count(), 1)
        res = self.api_client.put(self.detail_url, format='json',
            data=data, authentication=self.get_credentials())
        logger.debug("res=%s" % res)
        logger.debug("res.status_code=%s" % res.status_code)
        self.assertHttpAccepted(res)
        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(models.UserProfileParameter.objects.count(), 1)
        # Check for updated data.
        self.assertEqual(models.UserProfileParameter.objects.get(
            pk=self.userparam.pk).value, '43')

    def test_bad_credentials_json(self):
        cred = self.create_basic(username=self.username, password="badpasswd")
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get(self.detail_url, format='json',
            authentication=cred)
        self.assertHttpUnauthorized(resp)


class ContextResourceTest(ResourceTestCase):
    """
    """

    def setUp(self):
        super(ContextResourceTest, self).setUp()

        # Create a user.
        self.username = 'daniel'
        self.api_key = 'pass'
        self.password = 'pass'
        self.company = 'here'

        self.user = User.objects.create_user(self.username,
            'daniel@example.com', self.password)
        self.user_profile = models.UserProfile(user=self.user,
            company=self.company, nickname="danny")
        self.user_profile.save()



        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(
                codename="change_%s" % model_name)
            self.group.permissions.add(change_model)

        standard_group = Group.objects.get(name="standarduser")

        self.user.is_staff = True
        self.user.groups.add(standard_group)
        self.user.save()



        self.namespace1 = 'http://rmit.edu.au/schemas/hrmc'
        self.name1 = 'Foo'

        self.schema = models.Schema(namespace=self.namespace1,
            name=self.name1)
        self.schema.save()

        schema_data = {
            u'http://rmit.edu.au/schemas/hrmc':
                [u'the hrmc smart connector input values',
                {
                u'number_vm_instances': (models.ParameterName.NUMERIC, '', 7),
                u'iseed': (models.ParameterName.NUMERIC, '', 6),
                u'input_location': (models.ParameterName.STRING, '', 5),
                u'optimisation_scheme': (models.ParameterName.STRLIST, '', 4),
                u'threshold': (models.ParameterName.STRING, '', 3),  # FIXME: should be list of ints
                u'error_threshold': (models.ParameterName.STRING, '', 2),  # FIXME: should use float here
                u'max_iteration': (models.ParameterName.NUMERIC, '', 1),
                u'pottype': (models.ParameterName.NUMERIC, '', 0)
                }
                ],
            u'http://rmit.edu.au/schemas/system':
                [u'Information about the deployment platform',
                {
                u'platform': (models.ParameterName.STRING, '', 2),
                u'contextid': (models.ParameterName.NUMERIC, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/system/misc':
                [u'system level misc values',
                {
                u'transitions': (models.ParameterName.STRING, '', 4),  # deprecated
                u'system': (models.ParameterName.STRING, '', 3),
                u'id': (models.ParameterName.NUMERIC, '', 2),
                u'output_location': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/smartconnector_hrmc/files':
                 [u'the smartconnector hrmc input files',
                 {
                 }
                 ],
            }


        for ns in schema_data:
            l = schema_data[ns]
            logger.debug("l=%s" % l)
            desc = l[0]
            logger.debug("desc=%s" % desc)
            kv = l[1:][0]
            logger.debug("kv=%s", kv)

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



        self.platform, _ = models.Platform.objects.get_or_create(
            name='nectar', root_path='/home/centos')

        # Name our smart connector directive
        directive = models.Directive(name="hrmc")
        directive.save()

        composite_stage = models.Stage.objects.create(name="basic_connector",
             description="encapsulates a workflow",
             package="bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage",
             order=100)


        comm = models.Command(platform=self.platform, directive=directive, stage=composite_stage)
        comm.save()


        self.stage, _ = models.Stage.objects.get_or_create(name="testStage")
        self.context, _ = models.Context.objects.get_or_create(owner=self.user_profile,
            current_stage=composite_stage, deleted=True)
        self.detail_url = '/api/v1/context/{0}/?format=json'.format(self.context.pk)


    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    # def get_credentials(self):
    #     return self.create_digest(username=self.username,
    #         api_key=self.api_key, method="MD5", uri='/api/v1/userprofile/%s/' % self.pk)


    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)

        # We use ``assertKeys`` here to just verify the keys, not all the data.
        self.assertKeys(self.deserialize(resp), ['deleted', 'id', 'owner', 'resource_uri'])
        self.assertEqual(self.deserialize(resp)['owner'], '/api/v1/userprofile/{0}/'.format(self.user_profile.pk))


    def test_post_list(self):
        # Check how many are there first.
        self.assertEqual(models.Context.objects.count(), 1)

        # flexmock(hrmcstages).should_receive('make_runcontext_for_directive') \
        #     .and_return(({}, {}, models.Context(owner=self.user_profile,
        #         deleted=True, current_stage=self.stage)))


        self.post_data = {
                'number_vm_instances': 2,
                'iseed': 42,
                'input_location': 'file://127.0.0.1/hrmcrun/input_0',
                'optimisation_scheme': "MC",
                'threshold': "[1]",
                'error_threshold': "0.03",
                'max_iteration': 20,
                'pottype': 1,
                'output_location': 'foobar',
                'smart_connector': 'hrmc'}

        self.assertHttpCreated(self.api_client.post('/api/v1/context/?format=json',
            format='json', data=self.post_data,
            authentication=self.get_credentials()))
        # Verify a new one has been added.
        self.assertEqual(models.Context.objects.count(), 2) # mocked method does add.

        # TODO: as we mock out make_runcontext_for_directive, no way
        # to detect creation of new context.
        self.assertEqual(models.Context.objects.get(~Q(
            pk=self.context.pk)).current_stage.name, 'basic_connector')


    def test_bad_credentials_json(self):
        cred = self.create_basic(username=self.username, password="badpasswd")
        logger.debug("cred=%s" % cred)
        resp = self.api_client.get(self.detail_url, format='json',
            authentication=cred)
        self.assertHttpUnauthorized(resp)




