from django.conf import settings
from wheelcms_axle.models import Configuration
from wheelcms_axle.node import Node
from wheelcms_axle.toolbar import Toolbar
from django.core.urlresolvers import reverse



def configuration(request):
    """ make sure the 'config' context variable is always
        present since it contains information about the current
        theme """
    def is_logout_url():
        return request.path == reverse("userena_signout")

    return dict(config=Configuration.config(),
                settings=settings,
                root=Node.root(),
                is_logout_url=is_logout_url)

def toolbar(request):
    if request.user.is_authenticated():
        return dict(toolbar=Toolbar(Node.root(), request=request,
                                    status="special"))
    return dict()

