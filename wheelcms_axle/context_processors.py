from django.conf import settings
from wheelcms_axle.models import Configuration
from wheelcms_axle.node import Node
from wheelcms_axle.toolbar import Toolbar
from django.core.urlresolvers import reverse

from wheelcms_axle.utils import get_active_language


def languages(request):
    if len(settings.LANGUAGES) <= 1:
        return None

    current_language = get_active_language()
    current_label = dict(settings.LANGUAGES).get(current_language,
                                                 current_language)

    res = []

    ld = getattr(settings, 'LANGUAGE_DOMAINS', {})

    for lang, label in settings.CONTENT_LANGUAGES:
        if lang == current_language:
            is_current = True
        else:
            is_current = False

        url = Node.root().get_absolute_url(language=lang)
        has_translation = False

        domain = ld.get(lang)
        if domain:
            protocol = "https" if request.is_secure() else "http"
            url = "%s://%s%s" % (protocol, domain, url)

        res.append(dict(id=lang, label=label, url=url,
                        has_translation=has_translation,
                        is_current=is_current))
    return dict(languages=dict(current=dict(id=current_language, label=current_label),
                languages=res))

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

from .toolbar import get_toolbar
from warnings import warn


def toolbar(request):
    warn("wheelcms_axle.context_processors.toolbar is deprecated, "
     "please use wheelcms_axle.middleware.ToolbarMiddleware in stead",
     DeprecationWarning)
    if request.user.is_authenticated():
        return dict(toolbar=get_toolbar())
    return dict()

