from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^favicon.ico$', 'django.views.generic.simple.redirect_to',
                        {'url': '/static/images/favicon.ico'}),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^accounts/', include('userena.urls')),
    (r'^search/', include('haystack.urls')),
    (r'', include('wheelcms_axle.urls')),
)

