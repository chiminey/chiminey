from django.conf.urls import patterns, url, include

from django.contrib import admin
admin.autodiscover()

from bdphpcprovider.smartconnectorscheduler import views

urlpatterns = patterns('bdphpcprovider.smartconnectorscheduler',
    (r'^hello/$', views.hello),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^output/?P(<group_id>\d+)/(?P<file_id>\w+)/$', views.getoutput, name="getoutput")
)
