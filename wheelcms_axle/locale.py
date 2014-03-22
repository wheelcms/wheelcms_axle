"""
    Extended locale support for WheelCMS
"""

from threading import local
from django.utils import translation

_content_language = local()

def activate_content_language(language):
    _content_language.language = language

def get_content_language():
    if getattr(_content_language, 'language', None):
        return _content_language.language
    return translation.get_language()
