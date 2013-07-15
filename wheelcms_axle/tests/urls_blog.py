from django.conf.urls.defaults import patterns, include
from wheelcms_axle.urls import urlpatterns as wheelpatterns

urlpatterns = patterns('',
    (r'^blog/', include(wheelpatterns)),
)    
