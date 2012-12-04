from django.conf.urls import patterns, url, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'bdphpcprovider.smartconnectorscheduler.views.index'),
    url(r'^admin/', include(admin.site.urls)),
)
