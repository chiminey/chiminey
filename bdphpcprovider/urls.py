from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from bdphpcprovider.smartconnectorscheduler import views as scsviews
from bdphpcprovider.simpleui import views as uiviews


urlpatterns = patterns('',

    url(r'^accounts/login/$',  login, name="login"),
    url(r'^accounts/logout/$', logout, name="logout"),
    url(r'^$', 'django.views.generic.simple.redirect_to', {'url':  '/accounts/profile'}, name='home'),

    #url(r'^$', scsviews.hello),
    url(r'^accounts/profile/$', login_required(uiviews.UserProfileParameterListView.as_view()),
        name='userprofileparameter-list',),
    url(r'^accounts/profile/new/$', login_required(uiviews.CreateUserProfileParameterView.as_view()),
        name='userprofileparameter-new',),
    url(r'^accounts/profile/edit/(?P<pk>\d+)/$', login_required(uiviews.UpdateUserProfileParameterView.as_view()),
        name='userprofileparameter-edit',),
    url(r'^accounts/profile/delete/(?P<pk>\d+)/$', login_required(uiviews.DeleteUserProfileParameterView.as_view()),
        name='userprofileparameter-delete',),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^output/(?P<group_id>\w+)/(?P<file_id>[\w.]+)/$', scsviews.getoutput, name="getoutput"),
    url(r'^directive/(?P<directive_id>\d+)/$', scsviews.test_directive),

    url(r'^jobs/hrmc/new/$', login_required(uiviews.HRMCSubmitFormView.as_view()),
        name='hrmcjob-new',),
    url(r'^jobs/copy/new/$', login_required(uiviews.CopyFormView.as_view()),
        name='copyjob-new',),


    url(r'^jobs/$', login_required(uiviews.ContextList.as_view()),
        name='hrmcjob-list',),

    url(r'^job/(?P<pk>\d+)/$', login_required(uiviews.ContextView.as_view()),
        name='contextview',),

)
urlpatterns += staticfiles_urlpatterns()
