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
import functools
import logging
import json
import django
from pprint import pformat

# FIXME,TODO: replace basic authentication with basic+SSL,
# or better digest or oauth
from tastypie.authentication import (BasicAuthentication, ApiKeyAuthentication, MultiAuthentication)
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie import fields
from tastypie.resources import Resource, ModelResource, ALL_WITH_RELATIONS, ALL
from tastypie.utils import dict_strip_unicode_keys
from tastypie import http
from tastypie.bundle import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.paginator import Paginator

from django.db import transaction
from django.contrib.auth.models import User
from django import forms
from django.core.validators import ValidationError
from django.contrib.sessions.models import Session
from django.core.exceptions import MultipleObjectsReturned
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseNotAllowed,
    HttpResponseBadRequest)

from chiminey.smartconnectorscheduler.auth import logged_in_or_basicauth
from chiminey.platform import create_platform, update_platform, delete_platform
from chiminey.smartconnectorscheduler import models, serverside_validators
from chiminey.smartconnectorscheduler.errors import InvalidInputError
from chiminey.smartconnectorscheduler import jobs
from chiminey.smartconnectorscheduler.errors import deprecated


logger = logging.getLogger(__name__)


PARALLEL_PACKAGE= "chiminey.corestages.parent.Parent"


subtype_validation = {
    'password': ('string', serverside_validators.validate_string_not_empty,
                 forms.PasswordInput, None),
    'hidden': ('natural number', serverside_validators.validate_hidden, None, None),
    'string_not_empty': ('string_not_empty',
                         serverside_validators.validate_string_not_empty,
                         None, None),
    'natural': ('natural number', serverside_validators.validate_natural_number,
                None, None),
    'string': ('string', serverside_validators.validate_string, None, None),
    'whole': ('whole number', serverside_validators.validate_whole_number, None, None),
    'nectar_platform': ('NeCTAR platform name',
                        serverside_validators.validate_platform,
                        None, None),
    'storage_bdpurl': ('Storage platform name with optional offset path',
                        serverside_validators.validate_platform,
                        forms.TextInput, 255),
    'even': ('even number', serverside_validators.validate_even_number, None, None),
    'bdpurl': ('BDP url', serverside_validators.validate_BDP_url, forms.TextInput, 255),
    'float': ('floading point number', serverside_validators.validate_float_number,
              None, None),
    'jsondict': ('JSON Dictionary', serverside_validators.validate_jsondict,
                 forms.Textarea(attrs={'cols': 30, 'rows': 5}), None),
    'bool': ('On/Off', serverside_validators.validate_bool, None,  None),
    'platform': ('platform', serverside_validators.validate_platform,
                 None,  None),
    'mytardis': ('platform', serverside_validators.validate_platform,
                 None,  None),
    'choicefield': ('choicefield', functools.partial(
        serverside_validators.myvalidate_choice_field,
        choices=('MC', 'MCSA')), forms.Select(),  None),
    'timedelta': ('time delta: try 00:10:00, or 10 mins', serverside_validators.validate_timedelta, None, None),


}


class MyBasicAuthentication(BasicAuthentication):
    def __init__(self, *args, **kwargs):
        super(MyBasicAuthentication, self).__init__(*args, **kwargs)

    def is_authenticated(self, request, **kwargs):
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
        authentication = MultiAuthentication(ApiKeyAuthentication(), MyBasicAuthentication())
        authorization = DjangoAuthorization()

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def obj_create(self, bundle, **kwargs):
        return super(UserProfileResource, self).obj_create(bundle,
            user=bundle.request.user)

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
            'schema': ALL_WITH_RELATIONS,
            'namespace': ALL_WITH_RELATIONS,
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
        authentication = MultiAuthentication(
            ApiKeyAuthentication(),
            MyBasicAuthentication())
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']

    def get_object_list(self, request):
        return models.UserProfileParameterSet.objects.filter(
            user_profile__user=request.user)


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
        return models.UserProfileParameter.objects.filter(
            paramset__user_profile__user=request.user)

    class Meta:
        queryset = models.UserProfileParameter.objects.all()
        resource_name = 'userprofileparameter'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             MyBasicAuthentication())

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

    parent = fields.ForeignKey('self',
        attribute='parent', null=True)
    logger.debug('directive_name = %s' % directive)

    class Meta:
        queryset = models.Context.objects.all()
        resource_name = 'context'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             MyBasicAuthentication())
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post']
        paginator_class = Paginator

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def get_object_list(self, request):
        return models.Context.objects.filter(owner__user=request.user).order_by('-id')

    def post_list(self, request, **kwargs):
        #curl --user user2 --dump-header - -H "Content-Type: application/json" -X POST --data ' {"number_vm_instances": 8, "minimum_number_vm_instances": 8, "iseed": 42, "input_location": "file://127.0.0.1/myfiles/input", "optimisation_scheme": 2, "threshold": "[2]", "error_threshold": "0.03", "max_iteration": 10}' http://X.X.X.X/api/v1/context/?format=json

        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(request,
                                        body,
                                        format=request.META.get(
                                            'CONTENT_TYPE',
                                            'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized),
                                   request=request)
        bundle.data['username'] = request.user.username


        '''
        if 'smart_connector' in bundle.data:

            # TODO: need to parameterise API by set of directives
            dispatch_table = {
                'hrmc': self._post_to_hrmc,
                'sweep': self._post_to_sweep_hrmc,
                'sweep_make': self._post_to_sweep_make,
                'sweep_vasp': self._post_to_sweep_vasp,
                'copydir': self._post_to_copy,
                'remotemake': self._post_to_remotemake,
                'randomnumber': self._post_to_directive}
        '''


        if 'smart_connector' in bundle.data:
            smartconnector = bundle.data['smart_connector']
            logger.debug('smart_connector=%s' % smartconnector)
            directive_obj = models.Directive.objects.get(name=smartconnector)
            stage = directive_obj.stage
            logger.debug('stage=%s' % stage)
            sch = models.Schema.objects.get(namespace="http://rmit.edu.au/schemas/stages/sweep")
            logger.debug('sch=%s' % sch)
            subdirective = stage.get_stage_setting(sch, "directive")
            logger.debug('subdirective=%s' %subdirective)
            if subdirective:
                try:
                    (myplatform, directive_name,
                     directive_args, system_settings) = \
                    _post_to_sweep(bundle, smartconnector, subdirective)
                except Exception, e:
                    logger.error("post_list error %s" % e)
                    raise ImmediateHttpResponse(http.HttpBadRequest(e))
            else:
                # dispatch_table = {
                #     # 'sweep': self._post_to_sweep_hrmc,
                #     # 'sweep_make': self._post_to_sweep_make,
                #     # 'sweep_vasp': self._post_to_sweep_vasp,
                #     # 'copydir': self._post_to_copy,
                #     'hrmc': self._post_to_hrmc,
                #     # 'remotemake': self._post_to_remotemake,
                #     'randomnumber': self._post_to_directive}

                smart_connector = bundle.data['smart_connector']
                logger.debug("smart_connector=%s" % smart_connector)

                try:
                    logger.debug("dispatching %s" % smart_connector)
                    (myplatform, directive_name,
                    directive_args, system_settings) = _post_to_directive(bundle, smart_connector)
                    logger.debug("done")
                    # if smart_connector in dispatch_table:
                    #     logger.debug("dispatching %s" % smart_connector)
                    #     (myplatform, directive_name,
                    #     directive_args, system_settings) = dispatch_table[
                    #         smart_connector](bundle, smart_connector)
                    # else:
                    #     return http.HttpBadRequest()
                except Exception, e:
                    logger.error("post_list error %s" % e)
                    raise ImmediateHttpResponse(http.HttpBadRequest(e))
        location = []
        try:
            logger.debug(directive_args)
            (run_settings, command_args, run_context) \
                 = jobs.make_runcontext_for_directive(
                 myplatform,
                 directive_name,
                 directive_args, system_settings, request.user.username)

        except InvalidInputError, e:
            bundle.obj = None
            #messages.error(run_settings, e)
            logger.error(e)
            raise
        else:
            logger.debug("run_context=%s" % run_context)
            mess = "info, job started"
            # We bypass normal message interface because we want message to
            # appear before next page is rendered.
            message, was_created = models.ContextMessage.objects.get_or_create(
                context=run_context)
            message.message = mess
            message.save()
            bundle.obj.pk = run_context.id
            # We do not call obj_create because make_runcontext_for_directive()
            # has already created the object.
            location = self.get_resource_uri(bundle)

        return http.HttpCreated(location=location)

    # TODO: likely not allow hrmc to be called directly and will force through
    # sweep in all cases
    @deprecated
    def _post_to_hrmc(self, bundle, smart_connector):
        platform = 'nectar'
        directive_name = "hrmc"
        logger.debug("%s" % directive_name)
        directive_args = []

        try:
            directive_args.append(
             ['',
                 ['http://rmit.edu.au/schemas/hrmc',
                     ('number_vm_instances',
                         bundle.data[self.hrmc_schema + 'number_vm_instances']),
                     ('minimum_number_vm_instances',
                         bundle.data[self.hrmc_schema
                             + 'minimum_number_vm_instances']),
                     (u'iseed', bundle.data[self.hrmc_schema + 'iseed']),
                     ('max_seed_int', 1000),
                     (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
                     ('input_location',  bundle.data[self.hrmc_schema
                                                     + 'input_location']),
                     ('optimisation_scheme', bundle.data[self.hrmc_schema
                                                     + 'optimisation_scheme']),
                     ('threshold', str(bundle.data[self.hrmc_schema
                                                   + 'threshold'])),
                     ('error_threshold', str(bundle.data[self.hrmc_schema
                                                   + 'error_threshold'])),
                     ('max_iteration', bundle.data[self.hrmc_schema
                                                   + 'max_iteration']),
                     ('pottype', bundle.data[self.hrmc_schema + 'pottype'])
                 ]
             ])
        except KeyError, e:
            raise ImmediateHttpResponse(http.BadRequest(e))

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings',
                       u'output_location': bundle.data[
                            os.path.join(self.system_schema, 'output_location')]}#fixme: check whether location schema isused

        logger.debug('post_to_hrmc output_location = %s' % bundle.data[
            os.path.join(self.system_schema, 'output_location')])

        system_settings = {
            u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, system_settings)

    # TODO: likely not allow remotemake to be called directly and will
    # force through  sweep in all cases
    @deprecated
    def _post_to_remotemake(self, bundle, smart_connector):
        platform = 'nci'
        directive_name = "remotemake"
        logger.debug("%s" % directive_name)
        directive_args = []
        try:
            validate_input(bundle.data, directive_name)
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
                    ('input_location', bundle.data[
                        'http://rmit.edu.au/schemas/input/system/input_location']),
                    ('output_location', bundle.data[
                        'http://rmit.edu.au/schemas/input/system/output_location'])
                ],
                ['http://rmit.edu.au/schemas/input/mytardis',
                    #('experiment_id', bundle.data[self.hrmc_schema + 'experiment_id']),
                    ('experiment_id', 0),
                ],
            ])
        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % pformat(directive_args))
        return (platform, directive_name, directive_args, {})

    # FIXME,TOD: post_to_copy is out of date and should be updated to
    # use platforms etc.
    @deprecated
    def _post_to_copy(self, bundle, smart_connector):
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


def validate_input(data, directive_name):
    logger.debug(data)
    username = data['http://rmit.edu.au/schemas/bdp_userprofile/username']
    logger.debug(username)

    directive = models.Directive.objects.get(name=directive_name)
    for das in models.DirectiveArgSet.objects.filter(directive=directive):
        logger.debug("checking das=%s" % das)
        for param in models.ParameterName.objects.filter(schema=das.schema):
            logger.debug("checking param=%s" % param.name)
            value = data[os.path.join(das.schema.namespace, param.name)]
            # # FIXME: if a input field is blank, then may have been disabled.
            # # Therefore, we pass in initial default value, with assumption
            # # that it will be ignored anyway.  This might not be the best
            # # idea, because user that leaves field blank will get default value
            # # sent and not blank.  Therefore, fields cannot be blank.

            # if str(value) == "":
            #     logger.warn("skipping %s because disabled as input" % param.name)
            #     data[os.path.join(das.schema.namespace, param.name)] = param.initial
            #     logger.debug("data=%s" % data)
            #     continue;

            validator = subtype_validation[param.subtype][1]
            logger.debug("validator=%s" % validator)
            current_subtype = param.subtype
            logger.debug(current_subtype)
            if current_subtype in ['storage_bdpurl',
                                  'nectar_platform',
                                  'platform',
                                  'mytardis']:
                value = validator(value, username)
            else:
                value = validator(value)
            data[os.path.join(das.schema.namespace, param.name)] = value


def _post_to_sweep_hrmc(bundle, directive):
    return _post_to_sweep(bundle=bundle,
        directive=directive,
        subdirective="hrmc")


def _post_to_sweep_make(bundle, directive):
    return _post_to_sweep(bundle=bundle,
        directive=directive,
        subdirective="remotemake")


def _post_to_sweep_vasp(bundle, directive):
    return _post_to_sweep(bundle=bundle,
        directive=directive,
        subdirective="vasp")


def _post_to_sweep(bundle, directive, subdirective):
    logger.debug("_post_to_sweep for %s" % subdirective)
    platform = 'local'
    logger.debug("%s" % directive)

    try:
        validate_input(bundle.data, directive)
    except ValidationError, e:
        logger.error(e)
        raise
    directive_obj = models.Directive.objects.get(name=directive)
    dirargs = models.DirectiveArgSet.objects.filter(
        directive=directive_obj)
    schemas = [x.schema.namespace for x in dirargs]
    dargs = {}
    for key in bundle.data:
        if os.path.dirname(key) in schemas:
            d = dargs.setdefault(os.path.dirname(key), {})
            d[os.path.basename(key)] = bundle.data[key]

    logger.debug("dargs=%s" % pformat(dargs))

    d_arg = []
    for key in dargs:
        directive_arg = []
        directive_arg.append(key)
        for k, v in dargs[key].items():
            directive_arg.append((k, v))
        d_arg.append(directive_arg)

    d_arg.append(
    ['http://rmit.edu.au/schemas/system',
        # (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
        ('system', 'settings'),
        ('max_seed_int', 1000),
    ])
    # d_arg.append(
    # ['http://rmit.edu.au/schemas/stages/sweep',
    #     ('directive', subdirective)
    # ])
    d_arg.append(
    ['http://rmit.edu.au/schemas/bdp_userprofile',
        (u'username',
         str(bundle.data[
            'http://rmit.edu.au/schemas/bdp_userprofile/username'])),
    ])
    if not subdirective:
        subdirective = directive
    d_arg.append(
    ['http://rmit.edu.au/schemas/directive_profile',
        (u'directive_name', subdirective),
        (u'sweep_name', directive),
    ])
    directive_args = [''] + d_arg
    logger.debug("directive_args=%s" % pformat(directive_args))
    return (platform, directive, [directive_args], {})


def _post_to_directive(bundle, directive):
    platform = 'local'
    logger.debug("directive=%s" % directive)

    try:
        validate_input(bundle.data, directive)
    except ValidationError, e:
        logger.error(e)
        raise
    logger.debug("made past validation")
    directive_obj = models.Directive.objects.get(name=directive)
    dirargs = models.DirectiveArgSet.objects.filter(
        directive=directive_obj)
    schemas = [x.schema.namespace for x in dirargs]
    dargs = {}
    for key in bundle.data:
        if os.path.dirname(key) in schemas:
            d = dargs.setdefault(os.path.dirname(key), {})
            d[os.path.basename(key)] = bundle.data[key]

    logger.debug("dargs=%s" % pformat(dargs))

    d_arg = []
    for key in dargs:
        directive_arg = []
        directive_arg.append(key)
        for k, v in dargs[key].items():
            directive_arg.append((k, v))
        d_arg.append(directive_arg)

    d_arg.append(
    ['http://rmit.edu.au/schemas/system',
        (u'random_numbers', 'file://127.0.0.1/randomnums.txt'),
        ('system', 'settings'),
        ('max_seed_int', 1000),
    ])
    d_arg.append(
    ['http://rmit.edu.au/schemas/bdp_userprofile',
        (u'username',
         str(bundle.data[
            'http://rmit.edu.au/schemas/bdp_userprofile/username'])),
    ])
    d_arg.append(
    ['http://rmit.edu.au/schemas/directive_profile',
        (u'directive_name', directive),
    ])
    directive_args = [''] + d_arg
    logger.debug("directive_args=%s" % pformat(directive_args))
    return (platform, directive, [directive_args], {})


class ContextMessageResource(ModelResource):
    context = fields.ForeignKey(ContextResource,
        attribute="context", full=True, null=True)

    class Meta:
        queryset = models.ContextMessage.objects.all()
        resource_name = "contextmessage"
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             MyBasicAuthentication())
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']
        paginator_class = Paginator

    def get_object_list(self, request):
        return models.ContextMessage.objects.filter(
                context__owner__user=request.user)\
            .order_by('-context__parent__id', 'context__id')


class ContextParameterSetResource(ModelResource):
    context = fields.ForeignKey(ContextResource,
        attribute='context')
    schema = fields.ForeignKey(SchemaResource,
        attribute='schema')

    class Meta:
        queryset = models.ContextParameterSet.objects.all()
        resource_name = 'contextparameterset'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             MyBasicAuthentication())
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']

    def get_object_list(self, request):
        return models.ContextParameterSet.objects.filter(
            context__owner__user=request.user)

class PlatformParameterSetResource(ModelResource):
    schema = fields.ForeignKey(SchemaResource, attribute='schema', full=True)

    class Meta:
        queryset = models.PlatformParameterSet.objects.filter()
        resource_name = 'platformparamset'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = MultiAuthentication(ApiKeyAuthentication(),
            MyBasicAuthentication())
        #authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post']
        filtering = {
            'schema': ALL_WITH_RELATIONS,
            'owner': ALL_WITH_RELATIONS,
        }

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def post_list(self, request, **kwargs):
        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(
            request, body,
            format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(
            data=dict_strip_unicode_keys(deserialized), request=request)
        bundle.data['username'] = request.user.username
        try:
            if 'operation' in bundle.data:
                logger.debug('operation=%s' % bundle.data['operation'])
                operations = (
                    ('create', PlatformParameterSetResource._create_platform),
                    ('update', PlatformParameterSetResource._update_platform),
                    ('delete', PlatformParameterSetResource._delete_platform))
                for (x, y) in operations:
                    logger.debug("x=%s,y=%s" % (x, y))
                    if bundle.data['operation'] == x:
                        logger.debug("calling %s" % x)
                        done, message = y(self,bundle)
                        logger.debug("done=%s message=%s" % (done, message))
                        if not done:
                            response = http.HttpConflict()
                            response['message'] = message
                            return response
                        break
                else:
                    return http.HttpBadRequest()
                location = self.get_resource_uri(bundle)
            #     if bundle.data['operation'] == 'create':
            #         created, message = self.create_platform(bundle)
            #         if not created:
            #             response = http.HttpConflict()
            #             response['message'] = message
            #             return response
            #     elif bundle.data['operation'] == 'update':
            #         updated, message  = self.update_platform(bundle)
            #         if not updated:
            #             response = http.HttpConflict()
            #             response['message'] = message
            #             return response
            #     elif bundle.data['operation'] == 'delete':
            #         deleted, message = self.delete_platform(bundle)
            #         if not deleted:
            #             response = http.HttpConflict()
            #             response['message'] = message
            #             return response
            #     location = self.get_resource_uri(bundle)
            # else:
            #     return http.HttpBadRequest()
        except Exception, e:
            logger.error(bundle.data)
            logger.error(e)
            raise ImmediateHttpResponse(http.HttpBadRequest(e))
        response = http.HttpCreated(location=location)
        response['message'] = message
        return response

    def _create_platform(self, bundle):
        logger.debug("creating platform")
        username = bundle.data['username']
        schema_namespace = bundle.data['schema']
        parameters = bundle.data['parameters']
        platform_name = bundle.data['platform_name']
        created, message = create_platform(
            platform_name, username, schema_namespace, parameters)
        logger.debug('created=%s' % created)
        return created, message

    def _update_platform(self, bundle):
        username = bundle.data['username']
        updated_parameters = bundle.data['parameters']
        platform_name = bundle.data['platform_name']
        updated, message = update_platform(platform_name,
            username, updated_parameters)
        logger.debug('updated=%s' % updated)
        return updated, message

    def _delete_platform(self, bundle):
        username = bundle.data['username']
        platform_name = bundle.data['platform_name']
        deleted, message = delete_platform(platform_name, username)
        logger.debug('deleted=%s' % deleted)
        return deleted, message


class PlatformParameterResource(ModelResource):
    name = fields.ForeignKey(ParameterNameResource, attribute='name', full=True)
    paramset = fields.ForeignKey(PlatformParameterSetResource, attribute='paramset', full=True)

    class Meta:
        queryset = models.PlatformParameter.objects.all()
        resource_name = 'platformparameter'
        # TODO: FIXME: BasicAuth is horribly insecure without using SSL.
        # Digest is better, but configuration proved tricky.
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             MyBasicAuthentication())
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
        logger.debug("paramset owner=%s" % request.user.username)
        return models.PlatformParameter.objects.filter(
            paramset__schema__namespace__startswith=schema,
            paramset__owner__user__username=request.user.username)


def has_session_key(func):
    def wrapper(request, *args, **kwargs):
        if 'sessionid' in request.COOKIES:
            s = Session.objects.get(pk=request.COOKIES['sessionid'])
            if '_auth_user_id' in s.get_decoded():
                u = User.objects.get(id=s.get_decoded()['_auth_user_id'])
                request.user = u
                return func(request, *args, **kwargs)
        response = HttpResponse()
        response.status_code = 401
        return _error_response(
            response,
            "no session key found")
    return wrapper


def _error_response(response, msg):
    response.write('{"error": "%s"}' % msg)
    return response


def _preset_as_dict(request, ps):
    p_data = {}
    for pset in models.PresetParameterSet.objects.filter(preset=ps):
        for pp in models.PresetParameter.objects.filter(paramset=pset):
            p_data["%s/%s" % (pp.name.schema.namespace, pp.name.name)] = pp.value
    logger.debug("p_data=%s" % pformat(p_data))
    return p_data


def _delete_preset(request, pk):
    """ Deletes a prest by pk
        e.g., /coreapi/delete/4

    """
    user_profile = models.UserProfile.objects.get(user=request.user)
    try:
        ps = models.Preset.objects.get(id=pk, user_profile=user_profile)
    except models.Preset.DoesNotExist:
        return _error_response(
            HttpResponseNotFound(),
            "cannot get preset")
    except MultipleObjectsReturned:
        return _error_response(
            HttpResponseBadRequest(),
            "multiple presets returned")
    ps.delete()
    response = HttpResponse()
    response.status_code = 200
    return response


def _fix_put(request):
    """ As Django won't pass PUT values in request.PUT
    (see http://stackoverflow.com/questions/4994789/django-where-are-the-params-stored-on-a-put-delete-request)
    We cocerce these values into POST, which works because we only use
    strings for PUT data.
    """
    if request.method == "PUT":
        if hasattr(request, '_post'):
            del request._post
            del request._files
        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'
    request.PUT = request.POST




@has_session_key
@logged_in_or_basicauth()
@transaction.commit_on_success
def preset_list(request):
    # NB: Create REST-ish API for Presets rather than use tastypie because
    # latter doesn't handle non-model structural resources well.

    def post_preset(request):
        """
            Create a new Preset using POST
            e.g., /coreapi/preset/   {name:"presetname", directive="name of directive",
                data:'dictionary of full  schema/name strings and values'}
            returns location.
            Note that if data key is not a valid schema/name then that entry will
            dropped (silently). This is to stop spoofing of the form, and for
            if schema definition changes.
        """
        try:
            direct_name = request.POST['directive']
            data = request.POST['data']
            name = request.POST['name']
        except IndexError:
            return _error_response(
                HttpResponseBadRequest(),
                "cannot get input data")
        logger.debug("name=%s" % name)
        try:
            user_profile = models.UserProfile.objects.get(
                user=request.user)
        except models.UserProfile.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        logger.debug("user_profile=%s" % user_profile)
        if not user_profile:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        try:
            directive = models.Directive.objects.get(
                name=direct_name,
                hidden=False)
        except models.Directive.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get directive %s" % direct_name)
        logger.debug("directive=%s" % directive)
        if not directive:
            return HttpResponseNotFound()
        try:
            ps = models.Preset.objects.get(
                name=name,
                user_profile=user_profile)
        except models.Preset.DoesNotExist:
            pass
        else:
            return _error_response(
                HttpResponseBadRequest(),
                "preset with primary key %s already exists" % name)
        ps = models.Preset(
            name=name,
            user_profile=user_profile,
            directive=directive)
        ps.save()
        logger.debug("ps=%s" % ps)
        parameters = json.loads(data)
        logger.debug("parameters=%s" % pformat(parameters))
        new_pset = models.PresetParameterSet.objects.create(
            preset=ps, ranking=0)
        # TODO: we don't check types here
        logger.debug("new_pset=%s" % new_pset)
        for pp_k, pp_v in dict(parameters).items():
            logger.debug("pp_k=%s,pp_v=%s" % (pp_k, pp_v))
            schema_name, key = os.path.split(pp_k)
            if not schema_name or not key:
                logger.warn("Invalid parameter name %s" % pp_k)
                continue
            logger.debug("schema_name=%s" % schema_name)
            schema = None
            try:
                schema = models.Schema.objects.get(
                    namespace=schema_name)
            except models.Schema.DoesNotExist:
                logger.warn("cannot get schema for %s. Skipped"
                            % (schema.namespace))
                continue
            logger.debug("schema=%s" % schema)
            logger.debug("new_pset=%s" % new_pset)
            logger.debug("new_pset.id=%s" % new_pset.id)
            p_name = os.path.basename(pp_k)
            logger.debug("p_name=%s" % p_name)
            new_name = None
            try:
                # could cache this value for speed
                new_name = models.ParameterName.objects.get(
                    schema=schema,
                    name=p_name)
            except models.ParameterName.DoesNotExist:
                # if not valid pp_k, then we skip this entry.
                logger.warn("cannot get parametername for %s in %s. Skipped"
                 % (p_name, schema.namespace))
            else:
                logger.debug("new_name=%s" % new_name)
                try:
                    ppp = models.PresetParameter(
                        name=new_name,
                        paramset=new_pset,
                        value=pp_v)
                    ppp.save()
                    logger.debug("ppp=%s" % ppp)
                except Exception, e:
                    logger.error(e)
                    return _error_response(
                         HttpResponseBadRequest(),
                         "cannot create new object")
                logger.debug("done")
        response = HttpResponse()
        response['location'] = reverse('preset_detail', args=[ps.pk])
        response.status_code = 201
        return response

    def put_preset(request):
        """
            Updates a specific preset with new values based on "name" key
            e.g., /coreapi/preset/  {name:"...", directive:"...","data":"..."}
            deletes preset record which matches
            "location" contains uri of new record
        """
        _fix_put(request)
        try:
            name = request.POST['name']
            data = request.POST['data']
        except IndexError:
            return _error_response(
                HttpResponseBadRequest(),
                "cannot get input data")
        try:
            user_profile = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        logger.debug("user_profile=%s" % user_profile)
        if not user_profile:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        try:
            ps = models.Preset.objects.get(name=name,
                                           user_profile=user_profile)
        except models.Preset.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "preset %s not found" % name)
        except MultipleObjectsReturned:
            return _error_response(
                HttpResponseBadRequest(),
                "multiple presets with same key")

        parameters = json.loads(data)
        logger.debug("parameters=%s" % pformat(parameters))
        # TODO: we don't check types here, as all values are strings,
        # and we want to represent raw user-input.  When directive is
        # submitted, then validation will be performed.
        try:
            for pset in models.PresetParameterSet.objects.filter(preset=ps):
                logger.debug("pset=%s" % pset)
                for pp in models.PresetParameter.objects.filter(paramset=pset):
                    logger.debug("pp=%s" % pp)
                    full_name = "%s/%s" % (pp.name.schema.namespace, pp.name.name)
                    logger.debug("full_name=%s" % full_name)
                    if full_name in parameters:
                        pp.value = parameters[full_name]
                        logger.debug("parameters[pp.name.name]=%s"
                            % parameters[full_name])
                        pp.save()
        except Exception, e:
            logger.error(e)
            return _error_response(
                HttpResponseBadRequest(),
                "invalid input object")

        response = HttpResponse()
        response.status_code = 200
        return response

    def get_preset(request):
        """
        Retrieve current preset
        e.g.,   /coreapi/preset/
                returns set of all presets
                /coreapi/preset/?name=foo
                returns preset with name field equal to 'foo'
        """
        try:
            user_profile = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "user_profile not found")
        name = request.GET.get('name', '')
        directive = request.GET.get('directive', '')
        if name:
            # return by preset name
            try:
                ps = models.Preset.objects.get(
                    name=name,
                    user_profile=user_profile)
            except models.Preset.DoesNotExist:
                return _error_response(
                    HttpResponseNotFound(),
                    "preset not found")
            data = {}
            data['id'] = ps.id
            data['name'] = ps.name
            data['directive'] = ps.directive.name
            data['user'] = user_profile.user.username
            data['parameters'] = _preset_as_dict(request, ps)
        elif directive:
            # return all by directive name
            try:
                d = models.Directive.objects.get(name=directive)
            except models.Directive.DoesNotExist:
                return _error_response(
                    HttpResponseNotFound(),
                    "directive not found")
            ps = models.Preset.objects.filter(
                directive=d,
                user_profile=user_profile)
            data = []
            for p in ps:
                d = {}
                d['id'] = p.id
                d['name'] = p.name
                d['directive'] = p.directive.name
                d['user'] = user_profile.user.username
                d['parameters'] = _preset_as_dict(request, p)
                data.append(d)
        else:
            # return complete list
            user = user_profile.user.username
            data = []
            ps = models.Preset.objects.filter(
                    user_profile=user_profile)
            for p in ps:
                p_data = {}
                logger.debug("p=%s" % p)
                p_data['name'] = p.name
                p_data['id'] = p.id
                p_data['directive'] = p.directive.name
                p_data['user'] = user
                p_data['parameters'] = _preset_as_dict(request, p)
                data.append(p_data)

        logger.debug("data=%s" % data)
        return HttpResponse(json.dumps(data),
                        mimetype='application/json')

    for m, f in {'GET': get_preset, 'POST': post_preset,
                 'PUT': put_preset}.items():
        if request.method == m:
            response = f(request)
            logger.debug("response=%s" % response.status_code)
            return response
    return HttpResponseNotAllowed(['GET', 'POST', 'PUT'])


@has_session_key
@logged_in_or_basicauth()
def preset_detail(request, pk):

    def get_preset(request, pk):
        """
            Returns details for specific preset via GET
            e.g., /coreapi/preset/5/
        """
        try:
            user_profile = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        logger.debug("user_profile=%s" % user_profile)
        try:
            ps = models.Preset.objects.get(id=pk, user_profile=user_profile)
        except models.Preset.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "preset %s not found" % pk)
        except MultipleObjectsReturned:
            return _error_response(
                HttpResponseBadRequest(),
                "multiple objects with same key")
        data = {}
        data['id'] = ps.id
        data['name'] = ps.name
        data['directive'] = ps.directive.name
        data['user'] = user_profile.user.username
        data['parameters'] = _preset_as_dict(request, pk)
        return HttpResponse(json.dumps(data),
                        mimetype='application/json')

    def put_preset(request, pk):
        """
            Updates a specific preset with new values
            e.g., /coreapi/preset/5  {name:"...", directive:"...","data":"..."}
            deletes preset/5 record
            "location" contains uri of new record
        """
        _fix_put(request)
        try:
            data = request.POST['data']
        except Exception, e:
            logger.error(e)
            return _error_response(
                HttpResponseBadRequest(),
                "cannot get input data")
        logger.debug("data=%s" % data)
        try:
            user_profile = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "cannot get userprofile")
        logger.debug("user_profile=%s" % user_profile)
        try:
            ps = models.Preset.objects.get(id=pk, user_profile=user_profile)
        except models.Preset.DoesNotExist:
            return _error_response(
                HttpResponseNotFound(),
                "preset %s not found" % pk)
        except MultipleObjectsReturned:
            return _error_response(
                HttpResponseBadRequest(),
                "multiple objects with same key")
        parameters = json.loads(data)
        logger.debug("parameters=%s" % pformat(parameters))
        # TODO: we don't check types here
        try:
            for pset in models.PresetParameterSet.objects.filter(preset=ps):
                logger.debug("pset=%s" % pset)
                for pp in models.PresetParameter.objects.filter(paramset=pset):
                    logger.debug("pp=%s" % pp)
                    full_name = "%s/%s" % (pp.name.schema.namespace, pp.name.name)
                    logger.debug("full_name=%s" % full_name)
                    if full_name in parameters:
                        pp.value = parameters[full_name]
                        logger.debug("parameters[pp.name.name]=%s"
                            % parameters[full_name])
                        pp.save()
        except Exception, e:
            logger.error(e)
            return _error_response(
                HttpResponseBadRequest(),
                "invalid input object")
        response = HttpResponse()
        response.status_code = 200
        return response

    for m, f in {'GET': get_preset, 'PUT': put_preset,
            'DELETE': _delete_preset}.items():
        if request.method == m:
            return f(request, pk)
    return HttpResponseNotAllowed(['GET', 'POST', 'DELETE'])


@has_session_key
@logged_in_or_basicauth()
@transaction.commit_on_success
def new_directive(request):

    # def _make_schemas(directive_data):

    #     for ns in schema_data:
    #         l = schema_data[ns]
    #         logger.debug("l=%s" % l)
    #         desc = l[0]
    #         logger.debug("desc=%s" % desc)
    #         kv = l[1:][0]
    #         logger.debug("kv=%s", kv)

    #         url = urlparse(ns)

    #         context_schema, _ = models.Schema.objects.get_or_create(
    #             namespace=ns,
    #             defaults={'name': slugify(url.path.replace('/', ' ')),
    #                       'description': desc})

    #     for k, v in kv.items():
    #         try:
    #             model, _ = models.ParameterName.objects.get_or_create(
    #                 schema=context_schema,
    #                 name=k,
    #                 defaults=dict(v))
    #         except TypeError:
    #             logger.debug('Parameters are added to a schema using old format.')
    #         # if 'hidefield' in dict(v):
    #         #     hidelinks[model.id] = dict(v)['hidefield']

    def post_directive(request):
        if (request.user.groups.filter(name="admin").exists()
            or request.user.groups.is_superuser()):

            try:
                directive_data = request.POST['form']
                schemas_data = request.POST['formset_schema']
                input_schemas_data = request.POST['formset_input_schemas']
                stage_params_data = request.POST['formset_params']
                stage_set_data = request.POST['form_stage_set']

            except IndexError:
                return _error_response(
                    HttpResponseBadRequest(),
                    "cannot get input data")

            COMPOSITE_DESC = "Composite for the %(name)s connector"
            composite_stage, _ = models.Stage.objects.get_or_create(
                name="%s_composite" % directive_data['name'],
                description=COMPOSITE_DESC
                    % directive_data,
                package=PARALLEL_PACKAGE,
                order=100)

            composite_stage.update_settings({})

            directive_, _ = models.Directive.objects.get_or_create(
                name=directive_data['name'],
                description=directive_data['description'],
                hidden=directive_data['disabled'],
                stage=composite_stage)

            response = HttpResponse(request.POST)
            # response['location'] = reverse('preset_detail', args=[ps.pk])

            response.status_code = 201
            return response

        else:
            return _error_response(
                    HttpResponseBadRequest(),
                    "do not have access to this function")

    for m, f in {'POST': post_directive}.items():
        if request.method == m:
            response = f(request)
            logger.debug("response=%s" % response.status_code)
            return response
    return HttpResponseNotAllowed(['POST'])
