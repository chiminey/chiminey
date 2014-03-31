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
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from chiminey.simpleui import views as uiviews
from chiminey.simpleui.views import (
    computation_platform_settings,
    bdp_account_settings,
    storage_platform_settings
    )

from chiminey.simpleui.wizard.views import AddDirective1View
from chiminey.simpleui.wizard.views import AddDirective2View

from smartconnectorscheduler.views import (
    UserProfileResource,
    SchemaResource,
    ParameterNameResource,
    UserProfileParameterResource,
    UserProfileParameterSetResource,
    ContextResource,
 #   ContextInfoResource,
    ContextMessageResource,
    ContextParameterSetResource,
    UserResource,
    DirectiveResource,
    DirectiveArgSetResource,
    PlatformInstanceResource,
    PlatformParameterSetResource,
    PlatformParameterResource,
    # PresetResource,
    # PresetParameterSetResource,
    # PresetParameterResource
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
#v1_api.register(ContextInfoResource())
v1_api.register(ContextParameterSetResource())
v1_api.register(ContextMessageResource())
v1_api.register(DirectiveResource())
v1_api.register(DirectiveArgSetResource())
v1_api.register(PlatformInstanceResource())
v1_api.register(PlatformParameterSetResource())
v1_api.register(PlatformParameterResource())
# v1_api.register(PresetResource())
# v1_api.register(PresetParameterSetResource())
# v1_api.register(PresetParameterResource())


urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),
    ('^accounts/', include('django.contrib.auth.urls')),
    url(r'^$', uiviews.AboutView.as_view(), name="home"),
    url(r'^$', 'django.views.generic.simple.redirect_to', {'url':  '/'}, name='home'),
    url(r'^jobs/$', login_required(uiviews.get_contexts),
        name='hrmcjob-list',),
    url(r'^job/(?P<pk>\d+)/$', login_required(uiviews.ContextView.as_view()),
        name='contextview',),
    url(r'^jobs/directive/(?P<directive_id>\d+)/$', login_required(uiviews.submit_directive),
        name='makedirective',),
    url(r'^accounts/settings/bdp/$', login_required(bdp_account_settings),
        name='bdp-account-settings',),
    url(r'^accounts/settings/platform/computation/$', login_required(computation_platform_settings),
        name='computation-platform-settings',),
    url(r'^accounts/settings/platform/storage/$', login_required(storage_platform_settings),
        name='storage-platform-settings',),

    # url(r'^wizard/$', login_required(AddDirective1View.as_view()),
    #     name='wizard',),
    # url(r'^wizard2/$', login_required(AddDirective2View.as_view()),
    #     name='wizard2',),

    # # FIXME: this method is deprecated by list_jobs button.
    # url(r'^jobs/finished/edit/(?P<pk>\d+)/$', login_required(uiviews.FinishedContextUpdateView.as_view()),
    #     name='finishedcontext-edit',),

    # api urls
    url(r'^coreapi/', include('chiminey.smartconnectorscheduler.urls')),
    url(r'^api/', include(v1_api.urls)),

    #url(r'^login/$',  'django.contrib.auth.views.login', name="mylogin"),
    #url(r'^logout/$', 'django.contrib.auth.views.logout', name="mylogout"),
    # url(r'^accounts/profile/$', login_required(uiviews.UserProfileParameterListView.as_view()),
    #     name='userprofileparameter-list',),
    # url(r'^accounts/profile/new/$', login_required(uiviews.CreateUserProfileParameterView.as_view()),
    #     name='userprofileparameter-new',),
    # url(r'^accounts/profile/edit/(?P<pk>\d+)/$', login_required(uiviews.UpdateUserProfileParameterView.as_view()),
    #     name='userprofileparameter-edit',),
    # url(r'^accounts/profile/delete/(?P<pk>\d+)/$', login_required(uiviews.DeleteUserProfileParameterView.as_view()),
    #     name='userprofileparameter-delete',),
    # url(r'^jobs/$', login_required(uiviews.ContextList.as_view()),
    #     name='hrmcjob-list',),
    # url(r'^jobs/hrmc/new/$', login_required(uiviews.HRMCSubmitFormView.as_view()),
    #     name='hrmcjob-new',),
    # url(r'^jobs/sweep/new/$', login_required(uiviews.SweepSubmitFormView.as_view()),
    #     name='sweepjob-new',),
    # url(r'^jobs/pbs/new/$', login_required(uiviews.MakeSubmitFormView.as_view()),
    #     name='makejob-new',),
    # url(r'^jobs/copy/new/$', login_required(uiviews.CopyFormView.as_view()),
    #     name='copyjob-new',),
    # url(r'^list/$', login_required(uiviews.ListDirList.as_view()),
    #     name='listdir-list',),
    # url(r'^output/(?P<group_id>\w+)/(?P<file_id>[\w.]+)/$', scsviews.getoutput, name="getoutput"),
    # url(r'^directive/(?P<directive_id>\d+)/$', scsviews.test_directive),
)
urlpatterns += staticfiles_urlpatterns()
