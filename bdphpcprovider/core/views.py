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
import logging
import logging.config
logger = logging.getLogger(__name__)


from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.utils import dict_strip_unicode_keys
from tastypie import http


# FIXME,TODO: replace basic authentication with basic+SSL,
# or better digest or oauth
from tastypie.authentication import (BasicAuthentication)
from tastypie.authorization import DjangoAuthorization, Authorization
from bdphpcprovider.smartconnectorscheduler import models
from django.contrib.auth.models import User
import django

from pprint import pformat


from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError

from bdphpcprovider.smartconnectorscheduler import hrmcstages

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


class ParameterNameResource(ModelResource):
    schema = fields.ForeignKey(SchemaResource,
        attribute='schema')

    class Meta:
        queryset = models.ParameterName.objects.all()
        resource_name = 'parametername'
        allowed_methods = ['get']


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

    owner = fields.ForeignKey(UserProfileResource,
        attribute='owner')

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

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def get_object_list(self, request):
        return models.Context.objects.filter(owner__user=request.user)

    def post_list(self, request, **kwargs):
        #curl --user user2 --dump-header - -H "Content-Type: application/json" -X POST --data ' {"number_vm_instances": 8, "iseed": 42, "input_location": "file://127.0.0.1/myfiles/input", "number_dimensions": 2, "threshold": "[2]", "error_threshold": "0.03", "max_iteration": 10}' http://115.146.86.247/api/v1/context/?format=json

        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(request, body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)

        logger.debug('smart_connector=%s' % bundle.data['smart_connector'])
        logger.info('smart_connector=%s' % bundle.data['smart_connector'])

        if bundle.data['smart_connector'] == 'smartconnector_hrmc':
            (platform, directive_name,
             directive_args, system_settings) = self._post_to_hrmc(bundle)
        elif bundle.data['smart_connector'] == 'sweep':
            (platform, directive_name,
             directive_args, system_settings) = self._post_to_sweep(bundle)
        elif bundle.data['smart_connector'] == 'copydir':
            (platform, directive_name,
             directive_args, system_settings) = self._post_to_copy(bundle)

        location = []
        try:
            (run_settings, command_args, run_context) \
                 = hrmcstages.make_runcontext_for_directive(
                 platform,
                 directive_name,
                 directive_args, system_settings, request.user.username)

        except InvalidInputError,e:
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
        directive_name = "smartconnector_hrmc"
        logger.debug("%s" % directive_name)
        directive_args = []

        directive_args.append(
         ['',
             ['http://rmit.edu.au/schemas/hrmc',
                 ('number_vm_instances',
                     bundle.data['number_vm_instances']),
                 (u'iseed', bundle.data['iseed']),
                ('input_location',  bundle.data['input_location']),
                 ('number_dimensions', bundle.data['number_dimensions']),
                 ('threshold', str(bundle.data['threshold'])),
                 ('error_threshold', str(bundle.data['error_threshold'])),
                 ('max_iteration', bundle.data['max_iteration']),
                 ('pottype', bundle.data['pottype'])
             ]
         ])

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings', u'output_location': bundle.data['output_location']}

        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, system_settings)

    def _post_to_sweep(self, bundle):
        platform = 'local'
        directive_name = "sweep"
        logger.debug("%s" % directive_name)
        directive_args = []

        directive_args.append(
            ['',
                ['http://rmit.edu.au/schemas/hrmc',
                    ('number_vm_instances',
                        bundle.data['number_vm_instances']),
                    (u'iseed', bundle.data['iseed']),
                    ('input_location',  ''),
                    ('number_dimensions', bundle.data['number_of_dimensions']),
                    ('threshold', str(bundle.data['threshold'])),
                    ('error_threshold', str(bundle.data['error_threshold'])),
                    ('max_iteration', bundle.data['max_iteration']),
                    ('experiment_id', bundle.data['experiment_id']),
                    ('pottype', bundle.data['pottype'])],
                ['http://rmit.edu.au/schemas/stages/sweep',
                    ('input_location', bundle.data['input_location']),
                    ('sweep_map', bundle.data['sweep_map']),
                ],
                ['http://rmit.edu.au/schemas/stages/run',
                    ('run_map', bundle.data['run_map'])
                ]
            ])

        logger.debug("directive_args=%s" % pformat(directive_args))
        # make the system settings, available to initial stage and merged with run_settings

        system_dict = {
            u'system': u'settings',
            u'output_location': bundle.data['output_location']}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        return (platform, directive_name, directive_args, system_settings)

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