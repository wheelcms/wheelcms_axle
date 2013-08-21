from django.utils import translation

def get_url_for_language(o, language):
    """ assumes 'o' has a get_absolute_url """
    old = translation.get_language()
    translation.activate(language)
    url = o.get_absolute_url()
    translation.activate(old)
    return url

def get_active_language(request):
    if request:
        admin_language = request.session.get('admin_language')
        return admin_language or request.GET.get('language', translation.get_language())
    return translation.get_language()
