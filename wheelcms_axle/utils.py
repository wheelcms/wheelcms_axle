from django.utils import translation
from django.conf import settings

from wheelcms_axle import translate

def get_url_for_language(o, language):
    """ assumes 'o' has a get_absolute_url """
    old = translation.get_language()
    translation.activate(language)
    url = o.get_absolute_url()
    translation.activate(old)
    return url

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
