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

