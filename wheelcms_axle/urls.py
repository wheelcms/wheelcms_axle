from django.conf.urls import patterns, url, include
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

main_actions = "({0})".format("|".join(MainHandler.url_actions()))

urlpatterns += patterns('', 
    url("@/search", SearchHandler.as_view(), name="haystack_search"),

    ## Special url for configuration; issue #553
    url("@/configuration", ConfigurationHandler.as_view(), name="wheel_config"),


    ## nodepath with optional action. Should have higher precedence,
    ## else next entry will match as nodepath
    url("^(?P<nodepath>.*?)/(\+(?P<action>.+))?$",
        MainHandler.as_view(), name="wheel_main"),
    ## nodepath with optional handler
    url("^(?P<nodepath>.*?)/((?P<handlerpath>{0}))?$".format(main_actions),
        MainHandler.as_view(), name="wheel_main"),
    url("^(?P<handlerpath>{0})?$".format(main_actions),
        MainHandler.as_view(), name="wheel_main", kwargs={'nodepath':""}),
    # url("^$", MainHandler.as_view(), name="wheel_main", kwargs={'nodepath':""}),
    url("^\+(?P<action>.+)$", MainHandler.as_view(), name="wheel_main", kwargs={'nodepath':""}),

)
