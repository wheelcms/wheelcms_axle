from django.conf.urls import patterns, include

urlpatterns = patterns('',
    (r'^search/', include('haystack.urls')),
    (r'', include('wheelcms_axle.urls')),
)

