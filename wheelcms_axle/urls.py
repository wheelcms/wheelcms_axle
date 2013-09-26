from django.conf.urls.defaults import patterns, url, include
from two.ol.base import twpatterns
from wheelcms_axle.main import MainHandler, wheel_500, wheel_404
from wheelcms_axle.configuration import ConfigurationHandler
from wheelcms_axle.search import SearchHandler
from wheelcms_axle.sitemaps import ContentSitemap

from wheelcms_axle.userena_custom import UserenaDetailsFormExtra

handler500 = wheel_500
handler404 = wheel_404

urlpatterns = patterns('',
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': dict(default=ContentSitemap())}),
    (r'^robots\.txt$', 'wheelcms_axle.robots.robots_txt'),
    url(r'^accounts/(?P<username>[\.\w-]+)/edit/$',
       'userena.views.profile_edit',
       name='userena_profile_edit',
       kwargs={'edit_profile_form': UserenaDetailsFormExtra}),
    (r'^accounts/', include('userena.urls')),
)

urlpatterns += patterns('', 
    twpatterns("/@/search", SearchHandler, name="haystack_search"),

    ## Special url for configuration; issue #553
    twpatterns("/@/configuration", ConfigurationHandler, name="wheel_config"),

    ## operations on the root (no explicit instance, so pass it explicitly)
    twpatterns("/", MainHandler, name="wheel_main", instance=""),
    ## actions on the root, again pass instance explicitly
    twpatterns("/\+(?P<action>.+)", MainHandler, name="wheel_main", instance=""),

    ## operations on an instance. Instance can be resolved from path
    twpatterns(r"(?P<instance>.*)/\+(?P<action>.*)",
               MainHandler, name="wheel_main"),
    ## actions on an instance. Instance can be resolved from path
    twpatterns("(?P<instance>.+)", MainHandler, name="wheel_main"),
)
