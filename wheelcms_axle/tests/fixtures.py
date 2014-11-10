from django.contrib.auth.models import User
from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry, TypeRegistry
from wheelcms_axle.templates import TemplateRegistry, template_registry
from wheelcms_axle.registries.toolbar import (ToolbarActionRegistry,
                             toolbar_registry as original_toolbar_registry)

from wheelcms_axle.actions import ActionRegistry, action_registry

import pytest

@pytest.fixture()
def root():
    return Node.root()

@pytest.fixture()
def superuser(username="superuser", **kw):
    return User.objects.get_or_create(username=username,
                                      is_superuser=True, **kw)[0]
@pytest.fixture()
def toolbar_registry():
    registry = ToolbarActionRegistry()
    original_toolbar_registry.set(registry)
    return original_toolbar_registry

@pytest.fixture()
def localtyperegistry(request):
    registry = TypeRegistry()
    type_registry.set(registry)
    if hasattr(request.cls, 'type'):
        registry.register(request.cls.type)
    if hasattr(request.cls, 'other'):
        registry.register(request.cls.other)
    for type in getattr(request.cls, 'types', []):
        registry.register(type)
    for type in getattr(request.cls, 'extra_types', []):
        registry.register(type)

@pytest.fixture()
def localactionregistry(request):
    registry = ActionRegistry()
    action_registry.set(registry)

from wheelcms_axle.registries import core
from wheelcms_axle.workflows.default import DefaultWorkflow
from wheelcms_axle.registries.workflow import WorkflowRegistry

@pytest.fixture()
def defaultworkflow(request):
    old = core.workflow
    core.workflow = WorkflowRegistry()
    core.workflow.set_default(DefaultWorkflow)

    def fin():
        core.workflow = old

@pytest.fixture()
def localtemplateregistry(request):
    template_registry.set(TemplateRegistry())

from django.conf import settings

@pytest.fixture()
def multilang_ENNL(request):
    """ Provide a settings fixture with EN/NL configured """
    old_lang = settings.CONTENT_LANGUAGES
    old_fallback = settings.FALLBACK

    settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'),)#  ('fr', 'Francais'))
    settings.FALLBACK = 'en'

    def fin():
        settings.CONTENT_LANGUAGES = old_lang
        settings.FALLBACK = old_fallback
    request.addfinalizer(fin)

@pytest.fixture()
def multilang_ENNLFR(request):
    """ Provide a settings fixture with EN/NL configured """
    old_lang = settings.CONTENT_LANGUAGES
    old_fallback = settings.FALLBACK

    settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))
    settings.FALLBACK = 'en'

    def fin():
        settings.CONTENT_LANGUAGES = old_lang
        settings.FALLBACK = old_fallback
    request.addfinalizer(fin)

from django.utils import translation
from wheelcms_axle import locale

@pytest.fixture()
def active_language(request):
    old_lang = translation.get_language()
    def fin():
        translation.activate(old_lang)
        locale.activate_content_language(None)
    request.addfinalizer(fin)

