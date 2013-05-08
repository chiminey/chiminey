# Create your views here.

import logging
import logging.config
logger = logging.getLogger(__name__)


from tastypie import fields
from tastypie.resources import ModelResource

# TODO: replace basic authentication with oauth
from tastypie.authentication import DigestAuthentication
from tastypie.authorization import DjangoAuthorization
from bdphpcprovider.smartconnectorscheduler import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']


class UserProfileResource(ModelResource):
    userid = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = models.UserProfile.objects.all()
        resource_name = 'userprofile'
        allowed_methods = ['get']

    # def apply_authorization_limits(self, request, object_list):
    #     return object_list.filter(user=request.user)

    # def obj_create(self, bundle, **kwargs):
    #     return super(UserProfileResource, self).obj_create(bundle,
    #         user=bundle.request.user)

    def get_object_list(self, request):
        # res = super(UserProfileResource, self).get_object_list(request)
        # # if request.user is AnonymousUser:
        # #     return models.UserProfile.objects.none()
        # # logger.debug("res=%s" % res)
        # return res.filter(user=request.user
        # FIXME: we never seem to be authenticated here
        if request.user.is_authenticated():
            return models.UserProfile.objects.filter(user=request.user)
        else:
            return models.UserProfile.objects.none()


class SchemaResource(ModelResource):
    class Meta:
        queryset = models.ParameterName.objects.all()
        resource_name = 'schema'
        allowed_methods = ['get']


class ParameterNameResource(ModelResource):
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
        authentication = DigestAuthentication()
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
        authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']


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
        authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']


class ContextResource(ModelResource):
    owner = fields.ForeignKey(UserProfileResource,
        attribute='owner')

    class Meta:
        queryset = models.Context.objects.all()
        resource_name = 'context'
        authentication = DigestAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    def obj_create(self, bundle, **kwargs):
        return super(ContextResource, self).obj_create(bundle,
            user=bundle.request.user)

    def get_object_list(self, request):
        return models.Context.objects.filter(owner__user=request.user)



