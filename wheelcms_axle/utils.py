from django.utils import translation
from django.conf import settings

from wheelcms_axle import translate


def get_active_language(request=None):
    """
        The active language is either forced in settings,
        set in the session (for admin), a GET argument or
        the translation default
    """
    lang = getattr(settings, 'FORCE_LANGUAGE', None)

    if not lang and request:
        admin_language = request.session.get('admin_language')
        lang = admin_language or request.GET.get('language')

    if not lang:
        lang = translation.get_language()

    langids = (l[0] for l in translate.languages())

    if lang not in langids and getattr(settings, 'FALLBACK', None):
        lang = settings.FALLBACK
    return lang

from wheelcms_axle.stopwords import stopwords
import re

def generate_slug(name, language="en", max_length=100,
                  allowed="abcdefghijklmnopqrstuvwxyz0123456789_-",
                  default="slug"):
    """ generate a slug based on a title / sentence """
    name = name.lower()
    name_no_stopwords = " ".join(x for x in name.split()
                                 if x not in set(stopwords.get(language, [])))
    slug = re.sub("[^%s]+" % allowed, "-",
                          name_no_stopwords,
                          )[:max_length].strip("-")
    slug = re.sub("-+", "-", slug)
    return slug or default

