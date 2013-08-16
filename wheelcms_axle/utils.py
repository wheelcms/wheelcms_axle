from django.utils import translation

def get_url_for_language(o, language):
    """ assumes 'o' has a get_absolute_url """
    old = translation.get_language()
    translation.activate(language)
    url = o.get_absolute_url()
    translation.activate(old)
    return url

