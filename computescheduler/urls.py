from django.conf.urls import patterns, url, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^hello/$', 'computescheduler.scheduler.views.hello'),
    url(r'^admin/', include(admin.site.urls)),
)
