from django.conf.urls import patterns, url, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^hello/$', 'bdphpcprovider.smartconnectorscheduler.views.hello'),
    url(r'^admin/', include(admin.site.urls)),
)
