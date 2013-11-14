from wheelcms_axle.node import Node
from wheelcms_axle.content import TypeRegistry, type_registry
from wheelcms_axle.templates import TemplateRegistry, template_registry

import pytest

@pytest.fixture()
def root():
    return Node.root()

@pytest.fixture()
def localtyperegistry(request):
    registry = TypeRegistry()
    type_registry.set(registry)
    if hasattr(request.cls, 'type'):
        registry.register(request.cls.type)
    for type in getattr(request.cls, 'types', []):
        registry.register(type)

@pytest.fixture()
def localtemplateregistry(request):
    template_registry.set(TemplateRegistry())

from django.conf import settings

@pytest.fixture()
def multilang_ENNL(request):
    """ Provide a settings fixture with EN/NL configured """
    old_lang = settings.CONTENT_LANGUAGES
    old_fallback = settings.FALLBACK

    settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))
    settings.FALLBACK = 'en'

    def fin():
        settings.CONTENT_LANGUAGES = old_lang
        settings.FALLBACK = old_fallback
    request.addfinalizer(fin)

