from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from bdphpcprovider.smartconnectorscheduler import views as scsviews
from bdphpcprovider.simpleui import views as uiviews
from bdphpcprovider.simpleui.views import computation_platform_settings

from core.views import (
    UserProfileResource,
    SchemaResource,
    ParameterNameResource,
    UserProfileParameterResource,
    UserProfileParameterSetResource,
    ContextResource,
    UserResource,
    DirectiveResource,
    DirectiveArgSetResource,
    PlatformInstanceResource,
    PlatformInstanceParameterSetResource,
    PlatformInstanceParameterResource
    )
from tastypie.api import Api
v1_api = Api(api_name='v1')

v1_api.register(UserResource())
v1_api.register(UserProfileResource())
v1_api.register(SchemaResource())
v1_api.register(UserProfileParameterResource())
v1_api.register(UserProfileParameterSetResource())
v1_api.register(ParameterNameResource())
v1_api.register(ContextResource())
v1_api.register(DirectiveResource())
v1_api.register(DirectiveArgSetResource())
v1_api.register(PlatformInstanceResource())
v1_api.register(PlatformInstanceParameterSetResource())
v1_api.register(PlatformInstanceParameterResource())


urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),

    ('^accounts/', include('django.contrib.auth.urls')),
    #url(r'^login/$',  'django.contrib.auth.views.login', name="mylogin"),
    #url(r'^logout/$', 'django.contrib.auth.views.logout', name="mylogout"),
    url(r'^$', 'django.views.generic.simple.redirect_to', {'url':  '/accounts/login'}, name='home'),

    url(r'^accounts/profile/$', login_required(uiviews.UserProfileParameterListView.as_view()),
        name='userprofileparameter-list',),
    url(r'^accounts/profile/new/$', login_required(uiviews.CreateUserProfileParameterView.as_view()),
        name='userprofileparameter-new',),
    url(r'^accounts/profile/edit/(?P<pk>\d+)/$', login_required(uiviews.UpdateUserProfileParameterView.as_view()),
        name='userprofileparameter-edit',),
    url(r'^accounts/profile/delete/(?P<pk>\d+)/$', login_required(uiviews.DeleteUserProfileParameterView.as_view()),
        name='userprofileparameter-delete',),

    url(r'^jobs/$', login_required(uiviews.ContextList.as_view()),
        name='hrmcjob-list',),
    url(r'^job/(?P<pk>\d+)/$', login_required(uiviews.ContextView.as_view()),
        name='contextview',),
    url(r'^jobs/hrmc/new/$', login_required(uiviews.HRMCSubmitFormView.as_view()),
        name='hrmcjob-new',),
    url(r'^jobs/sweep/new/$', login_required(uiviews.SweepSubmitFormView.as_view()),
        name='sweepjob-new',),
    url(r'^jobs/pbs/new/$', login_required(uiviews.MakeSubmitFormView.as_view()),
        name='makejob-new',),

    url(r'^jobs/directive/(?P<directive_id>\d+)/$', login_required(uiviews.submit_directive),
        name='makedirective',),

    url(r'^jobs/copy/new/$', login_required(uiviews.CopyFormView.as_view()),
        name='copyjob-new',),

    url(r'^list/$', login_required(uiviews.ListDirList.as_view()),
        name='listdir-list',),

    url(r'^accounts/settings/$', login_required(computation_platform_settings),
        name='account-settings',),

    url(r'^output/(?P<group_id>\w+)/(?P<file_id>[\w.]+)/$', scsviews.getoutput, name="getoutput"),
    url(r'^directive/(?P<directive_id>\d+)/$', scsviews.test_directive),


    url(r'^jobs/finished/edit/(?P<pk>\d+)/$', login_required(uiviews.FinishedContextUpdateView.as_view()),
        name='finishedcontext-edit',),

    url(r'^api/', include(v1_api.urls)),
)
urlpatterns += staticfiles_urlpatterns()
