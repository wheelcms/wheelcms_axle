from wheelcms_axle.models import Configuration
from django.conf import settings

def configuration(request):
    """ make sure the 'config' context variable is always
        present since it contains information about the current
        theme """
    return dict(config=Configuration.config(),
                settings=settings)
