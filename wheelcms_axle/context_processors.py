from django.conf import settings
from wheelcms_axle.models import Configuration
from wheelcms_axle.node import Node
from wheelcms_axle.toolbar import Toolbar


def configuration(request):
    """ make sure the 'config' context variable is always
        present since it contains information about the current
        theme """
    return dict(config=Configuration.config(),
                settings=settings)

def toolbar(request):
    if request.user.is_authenticated():
        return dict(toolbar=Toolbar(Node.root(), request=request,
                                    status="special"))
    return dict()

