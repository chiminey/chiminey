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
#
#
#
import os
import logging
import django
from pprint import pformat

# FIXME,TODO: replace basic authentication with basic+SSL,
# or better digest or oauth
from tastypie.authentication import (BasicAuthentication)
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, ALL
from tastypie.utils import dict_strip_unicode_keys
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.paginator import Paginator
from django.contrib.auth.models import User
from django.core.validators import ValidationError
from django import forms

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import platform


logger = logging.getLogger(__name__)


# TODO: this code should be copied to maintain separation between api/ui
from bdphpcprovider.simpleui import validators

logger = logging.getLogger(__name__)


class MyBasicAuthentication(BasicAuthentication):
    def __init__(self, *args, **kwargs):
        super(MyBasicAuthentication, self).__init__(*args, **kwargs)

    def is_authenticated(self, request, **kwargs):
        from django.contrib.sessions.models import Session
        if 'sessionid' in request.COOKIES:
            s = Session.objects.get(pk=request.COOKIES['sessionid'])
            if '_auth_user_id' in s.get_decoded():
                u = User.objects.get(id=s.get_decoded()['_auth_user_id'])
                request.user = u
                return True
        return super(MyBasicAuthentication, self).is_authenticated(request, **kwargs)



class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        allowed_methods = ['get']
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']


class UserProfileResource(ModelResource):
    userid = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = models.UserProfile.objects.all()
        resource_name = 'userprofile'
        allowed_methods = ['get']
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        authorization = DjangoAuthorization()

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    # def obj_create(self, bundle, **kwargs):
    #     return super(UserProfileResource, self).obj_create(bundle,
    #         user=bundle.request.user)

    def get_object_list(self, request):
        # FIXME: we never seem to be authenticated here
        if request.user.is_authenticated():
            return models.UserProfile.objects.filter(user=request.user)
        else:
            return models.UserProfile.objects.none()


class SchemaResource(ModelResource):
    class Meta:
        queryset = models.Schema.objects.all()
        resource_name = 'schema'
        allowed_methods = ['get']
        filtering = {
            'schema': ALL_WITH_RELATIONS
        }


class DirectiveResource(ModelResource):
    class Meta:
        queryset = models.Directive.objects.all()
        resource_name = 'directive'
        allowed_methods = ['get']


class DirectiveArgSetResource(ModelResource):
    schema = fields.ForeignKey(SchemaResource,
        attribute='schema')
    directive = fields.ForeignKey(DirectiveResource,
        attribute='directive')
    class Meta:
        queryset = models.DirectiveArgSet.objects.all()
        resource_name = 'directiveargset'
        allowed_methods = ['get']
        filtering = {
            'directive': ALL_WITH_RELATIONS,
        }

class ParameterNameResource(ModelResource):
    schema = fields.ForeignKey(SchemaResource,
        attribute='schema')

    class Meta:
        queryset = models.ParameterName.objects.all()
        resource_name = 'parametername'
        allowed_methods = ['get']
        filtering = {
            'schema': ALL_WITH_RELATIONS
        }


class UserProfileParameterSetResource(ModelResource):
    user_profile = fields.ForeignKey(UserProfileResource,
        attribute='user_profile')
    schema = fields.ForeignKey(SchemaResource,
        attribute='schema')

    class Meta:
        queryset = models.UserProfileParameterSet.objects.all()
        resource_name = 'userprofileparameterset'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']

    def get_object_list(self, request):
        return models.UserProfileParameterSet.objects.filter(user_profile__user=request.user)


class UserProfileParameterResource(ModelResource):
    name = fields.ForeignKey(ParameterNameResource,
        attribute='name')
    paramset = fields.ForeignKey(UserProfileParameterSetResource,
        attribute='paramset')

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(paramset__user_profile__user=request.user)

    def obj_create(self, bundle, **kwargs):
        return super(UserProfileParameterResource, self).obj_create(bundle,
            user=bundle.request.user)

    def get_object_list(self, request):
        return models.UserProfileParameter.objects.filter(paramset__user_profile__user=request.user)

    class Meta:
        queryset = models.UserProfileParameter.objects.all()
        resource_name = 'userprofileparameter'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        # curl --digest --user user2 --dump-header - -H "Content-Type: application/json" -X PUT --data ' {"value": 44}' http://115.146.86.247/api/v1/userprofileparameter/48/?format=json
        allowed_methods = ['get', 'put']
        # TODO: validation on put value to correct type


class ContextResource(ModelResource):
    hrmc_schema = "http://rmit.edu.au/schemas/input/hrmc/"
    system_schema = "http://rmit.edu.au/schemas/input/system"
    sweep_schema = 'http://rmit.edu.au/schemas/input/sweep/'

    owner = fields.ForeignKey(UserProfileResource,
        attribute='owner')

    directive = fields.ForeignKey(DirectiveResource,
        attribute='directive', full=True, null=True)

    class Meta:
        queryset = models.Context.objects.all()
        resource_name = 'context'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        authentication = MyBasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post']
        paginator_class = Paginator

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def get_object_list(self, request):
        return models.Context.objects.filter(owner__user=request.user).order_by('-id')

    def post_list(self, request, **kwargs):
        #curl --user user2 --dump-header - -H "Content-Type: application/json" -X POST --data ' {"number_vm_instances": 8, "minimum_number_vm_instances": 8, "iseed": 42, "input_location": "file://127.0.0.1/myfiles/input", "number_dimensions": 2, "threshold": "[2]", "error_threshold": "0.03", "max_iteration": 10}' http://115.146.86.247/api/v1/context/?format=json

        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(request, body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)
        try:
            if 'smart_connector' in bundle.data:
                # TODO: generalise this
                logger.debug('smart_connector=%s' % bundle.data['smart_connector'])
                if bundle.data['smart_connector'] == 'hrmc':
                    (platform, directive_name,
                     directive_args, system_settings) = self._post_to_hrmc(bundle)
                elif bundle.data['smart_connector'] == 'sweep':
                    (platform, directive_name,
                     directive_args, system_settings) = self._post_to_sweep(bundle)
                elif bundle.data['smart_connector'] == 'copydir':
                    (platform, directive_name,
                     directive_args, system_settings) = self._post_to_copy(bundle)
                elif bundle.data['smart_connector'] == 'remotemake':
                        (platform, directive_name,
                         directive_args, system_settings) = self._post_to_remotemake(bundle)
            else:
                return http.HttpBadRequest()
        except Exception, e:
            logger.error(e)
            raise ImmediateHttpResponse(http.HttpBadRequest(e))
            #return self.create_response(request, bundle, response_class=http.HttpForbidden)
        location = []
        try:
            (run_settings, command_args, run_context) \
                 = hrmcstages.make_runcontext_for_directive(
                 platform,
                 directive_name,
                 directive_args, system_settings, request.user.username)

        except InvalidInputError, e:
            bundle.obj = None
            logger.error(e)
        else:
            logger.debug("run_context=%s" % run_context)
            bundle.obj.pk = run_context.id
            # We do not call obj_create because make_runcontext_for_directive()
            # has already created the object.

            location = self.get_resource_uri(bundle)

        return http.HttpCreated(location=location)

    def _post_to_hrmc(self, bundle):
        platform = 'nectar'
        directive_name = "hrmc"
        logger.debug("%s" % directive_name)
        directive_args = []

        try:
            directive_args.append(
             ['',
                 ['http://rmit.edu.au/schemas/hrmc',
                     ('number_vm_instances',
                         bundle.data[self.hrmc_schema+'number_vm_instances']),
                     ('minimum_number_vm_instances',
                         bundle.data[self.hrmc_schema+'minimum_number_vm_instances']),
                     (u'iseed', bundle.data[self.hrmc_schema+'iseed']),
                     ('max_seed_int', 1000),
                     (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
                     ('input_location',  bundle.data[self.hrmc_schema+'input_location']),
                     ('number_dimensions', bundle.data[self.hrmc_schema+'number_dimensions']),
                     ('threshold', str(bundle.data[self.hrmc_schema+'threshold'])),
                     ('error_threshold', str(bundle.data[self.hrmc_schema+'error_threshold'])),
                     ('max_iteration', bundle.data[self.hrmc_schema+'max_iteration']),
                     ('pottype', bundle.data[self.hrmc_schema+'pottype'])
                 ]
             ])
        except KeyError, e:
            raise ImmediateHttpResponse(http.BadRequest(e))

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings', u'output_location': bundle.data[self.system_schema+'output_location']}

        logger.debug('post_to_hrmc output_location = %s' % bundle.data[self.system_schema+'output_location'])

        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, system_settings)

    def validate_input(self, data, directive_name):

        subtype_validation = {
            'natural': ('natural number', validators.validate_natural_number, None, None),
            'string': ('string', validators.validate_string, None, None),
            'whole': ('whole number', validators.validate_whole_number, None, None),
            'even': ('even number', validators.validate_even_number, None, None),
            'bdpurl': ('BDP url', validators.validate_BDP_url, forms.TextInput, 255),
            'float': ('floading point number', validators.validate_float_number, None, None),
            'jsondict': ('JSON Dictionary', validators.validate_jsondict, forms.Textarea(attrs={'cols':30, 'rows': 5}), None),
            'bool': ('On/Off', validators.validate_bool, None,  None),

        }
        directive = models.Directive.objects.get(name=directive_name)
        for das in models.DirectiveArgSet.objects.filter(directive=directive):
            for param in models.ParameterName.objects.filter(schema=das.schema):
                value = data[os.path.join(das.schema.namespace, param.name)]
                validator = subtype_validation[param.subtype][1]
                value = validator(value)

    def _post_to_sweep(self, bundle):
        platform = 'local'
        directive_name = "sweep"
        logger.debug("%s" % directive_name)
        directive_args = []

        try:
            self.validate_input(bundle.data, directive_name)
        except ValidationError, e:
            logger.error(e)
            raise

        directive_args.append(
            ['',
                ['http://rmit.edu.au/schemas/input/hrmc',
                    ('pottype', bundle.data[self.hrmc_schema + 'pottype']),
                    ('max_iteration', bundle.data[self.hrmc_schema + 'max_iteration']),
                    ('error_threshold', str(bundle.data[self.hrmc_schema + 'error_threshold'])),
                    ('threshold', str(bundle.data[self.hrmc_schema + 'threshold'])),
                    ('number_dimensions', bundle.data[self.hrmc_schema + 'number_dimensions']),
                    ('iseed', bundle.data[self.hrmc_schema + 'iseed']),
                    ('fanout_per_kept_result', bundle.data[self.hrmc_schema + 'fanout_per_kept_result']),
                ],
                ['http://rmit.edu.au/schemas/input/sweep',
                    ('sweep_map', bundle.data[self.sweep_schema + 'sweep_map']),
                ],
                ['http://rmit.edu.au/schemas/stages/sweep',
                    ('directive', 'hrmc')
                ],
                ['http://rmit.edu.au/schemas/input/reliability',
                    ('maximum_retry',
                        bundle.data['http://rmit.edu.au/schemas/input/reliability/' + 'maximum_retry']),
                    ('reschedule_failed_processes',
                        int(bundle.data['http://rmit.edu.au/schemas/input/reliability/' + 'reschedule_failed_processes'])),
                ],
                ['http://rmit.edu.au/schemas/input/system/cloud',
                    ('number_vm_instances',
                        bundle.data['http://rmit.edu.au/schemas/input/system/cloud/number_vm_instances']),
                    ('minimum_number_vm_instances',
                        bundle.data['http://rmit.edu.au/schemas/input/system/cloud/minimum_number_vm_instances']),
                ],
                ['http://rmit.edu.au/schemas/system',
                    (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
                    ('system', 'settings'),
                    ('max_seed_int', 1000),
                ],
                ['http://rmit.edu.au/schemas/input/system',
                    ('input_location', bundle.data['http://rmit.edu.au/schemas/input/system/input_location']),
                    ('output_location', bundle.data['http://rmit.edu.au/schemas/input/system/output_location'])
                ],
                ['http://rmit.edu.au/schemas/input/mytardis',
                    #('experiment_id', bundle.data[self.hrmc_schema + 'experiment_id']),
                    ('experiment_id', 0),
                ],
                ['http://rmit.edu.au/schemas/stages/run',
                    #('run_map', bundle.data['run_map'])
                    ('run_map', "{}")
                ],
            ])

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, {})

    def _post_to_remotemake(self, bundle):
        platform = 'nci'
        directive_name = "remotemake"
        logger.debug("%s" % directive_name)
        directive_args = []

        try:
            self.validate_input(bundle.data, directive_name)
        except ValidationError, e:
            logger.error(e)
            raise

        directive_args.append(
            ['',

                ['http://rmit.edu.au/schemas/input/sweep',
                    ('sweep_map', bundle.data[self.sweep_schema + 'sweep_map']),
                ],
                ['http://rmit.edu.au/schemas/system',
                    (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
                    ('system', 'settings'),
                    ('max_seed_int', 1000),
                ],
                ['http://rmit.edu.au/schemas/input/system',
                    ('input_location', bundle.data['http://rmit.edu.au/schemas/input/system/input_location']),
                    ('output_location', bundle.data['http://rmit.edu.au/schemas/input/system/output_location'])
                ],
                ['http://rmit.edu.au/schemas/input/mytardis',
                    #('experiment_id', bundle.data[self.hrmc_schema + 'experiment_id']),
                    ('experiment_id', 0),
                ],
            ])

        #remotemake_schema = "http://rmit.edu.au/schemas/remotemake`"
        # directive_args.append(
        #     ['',
        #         ['http://rmit.edu.au/schemas/remotemake',
        #             ('input_location',  bundle.data[remotemake_schema+'input_location']),
        #             ('experiment_id', bundle.data[remotemake_schema+'experiment_id'])],
        #         ['http://rmit.edu.au/schemas/stages/make',
        #             ('sweep_map', bundle.data[self.sweep_schema+'sweep_map'])]])

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings

        # system_dict = {
        #     u'system': u'settings',
        #     u'output_location': bundle.data[self.system_schema+'output_location']}
        # system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, {})

    def _post_to_copy(self, bundle):
        platform = 'nci'  # FIXME: should be local, why local Ian?
        directive_name = "copydir"
        logger.debug("%s" % directive_name)
        directive_args = []

        directive_args.append([bundle.data['source_bdp_url'], []])
        directive_args.append([bundle.data['destination_bdp_url'], []])


        logger.debug("directive_args=%s" % pformat(directive_args))

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, system_settings)


class PlatformInstanceResource(ModelResource):
    class Meta:
        queryset = models.PlatformInstance.objects.all()
        resource_name = 'platform'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        authentication = MyBasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)


class PlatformInstanceParameterSetResource(ModelResource):
    platform = fields.ForeignKey(PlatformInstanceResource, attribute='platform', full=True)
    schema = fields.ForeignKey(SchemaResource, attribute='schema', full=True)

    class Meta:
        queryset = models.PlatformInstanceParameterSet.objects.all()
        resource_name = 'platformparamset'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        authentication = MyBasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post']
        filtering = {
            'platform': ALL_WITH_RELATIONS,
            'schema': ALL_WITH_RELATIONS,
        }

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)


    def post_list(self, request, **kwargs):
        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(request, body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)
        bundle.data['username'] = request.user.username
        try:
            if 'operation' in bundle.data:
                logger.debug('operation=%s' % bundle.data['operation'])
                if bundle.data['operation'] == 'create':
                    created, message = self.create_platform(bundle)
                    if not created:
                        response = http.HttpConflict()
                        response['message'] = message
                        return response
                elif bundle.data['operation'] == 'update':
                    updated, message  = self.update_platform(bundle)
                    if not updated:
                        response = http.HttpConflict()
                        response['message'] = message
                        return response
                elif bundle.data['operation'] == 'delete':
                    deleted, message = self.delete_platform(bundle)
                    if not deleted:
                        response = http.HttpConflict()
                        response['message'] = message
                        return response
                location = self.get_resource_uri(bundle)
            else:
                return http.HttpBadRequest()
        except Exception, e:
            logger.error(e)
            raise ImmediateHttpResponse(http.HttpBadRequest(e))
        response = http.HttpCreated(location=location)
        response['message'] = message
        return response

    def create_platform(self, bundle):
        username = bundle.data['username']
        schema = bundle.data['schema']
        parameters = bundle.data['parameters']
        created, message = platform.create_platform_paramset(
            username, schema, parameters)
        logger.debug('created=%s' % created)
        return created, message

    def update_platform(self, bundle):
        username = bundle.data['username']
        schema = bundle.data['schema']
        filters = bundle.data['filters']
        updated_parameters = bundle.data['parameters']
        updated, message = platform.update_platform_paramset(
            username, schema, filters, updated_parameters)
        logger.debug('updated=%s' % updated)
        return updated, message

    def delete_platform(self, bundle):
        username = bundle.data['username']
        schema = bundle.data['schema']
        filters = bundle.data['filters']
        deleted, message  = platform.delete_platform_paramsets(username, schema, filters)
        logger.debug('deleted=%s' % deleted)
        return deleted, message


class PlatformInstanceParameterResource(ModelResource):
    name = fields.ForeignKey(ParameterNameResource, attribute='name', full=True)
    paramset = fields.ForeignKey(PlatformInstanceParameterSetResource, attribute='paramset', full=True)

    class Meta:
        queryset = models.PlatformInstanceParameter.objects.all()
        resource_name = 'platformparameter'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = BasicAuthentication()
        authentication = MyBasicAuthentication()
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']
        filtering = {
            'name': ALL_WITH_RELATIONS,
            'paramset': ALL_WITH_RELATIONS,
        }

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)


    def get_object_list(self, request):
        from urlparse import urlparse, parse_qsl
        url = urlparse(request.META['REQUEST_URI'])
        query = parse_qsl(url.query)
        query_settings = dict(x[0:] for x in query)
        logger.debug('query=%s' % query)
        logger.debug('query_settings=%s' % query_settings)
        schema = query_settings['schema']
        return models.PlatformInstanceParameter.objects.filter(
            paramset__schema__namespace__startswith=schema)

