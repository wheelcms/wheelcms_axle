from django.conf.urls.defaults import patterns
from two.ol.base import twpatterns
from wheelcms_axle.main import MainHandler
from wheelcms_axle.configuration import ConfigurationHandler

urlpatterns = patterns('',
    ## handle /@/create for creation under root
    twpatterns("@", MainHandler, name="wheel_main", parent=""),
    ## handle direct root access
    twpatterns("/@/configuration", ConfigurationHandler, name="wheel_config"),
    twpatterns("/", MainHandler, name="wheel_main", instance=""),
    ## handle /path/@/create for creation somewhere deeped
    twpatterns("(?P<parent>.*)/@", MainHandler, name="wheel_main"),
    ## don't really need this? /<instance>/op works fine...
    twpatterns("(?P<parent>.*)/@/(?P<instance>[^/]*)", MainHandler, name="wheel_main"),
    ## for basic node access:
    twpatterns("(?P<instance>.*)", MainHandler, name="wheel_main"),
)
