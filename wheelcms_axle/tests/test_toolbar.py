"""
    Test the toolbar class
"""
from wheelcms_axle.models import Node, type_registry, TypeRegistry
from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle.tests.models import Type1, Type1Type, Type2Type

from wheelcms_spokes.models import Spoke

class TestToolbar(object):
    """
        Test toolbar child restrictions, context buttons
    """
    def setup(self):
        self.registry = TypeRegistry()
        type_registry.set(self.registry)
        self.registry.register(Type1Type)
        self.registry.register(Type2Type)

    def allchildren(self, children):
        """ match against all registered children """
        return set(x['name'] for x in children) == \
               set(c.name() for c in type_registry.values())

    def test_unconnected(self, client):
        """
            Test behaviour on unconnected node - allow
            creation of all types of sub content
        """
        root = Node.root()
        toolbar = Toolbar(root, "view")
        assert toolbar.show_create()
        assert self.allchildren(toolbar.children())

    def test_connected_no_restrictions(self, client):
        """
            A node with content without restrictions
        """
        root = Node.root()
        content = Type1(node=root)
        content.save()
        toolbar = Toolbar(root, "view")
        assert toolbar.show_create()
        assert self.allchildren(toolbar.children())

    def test_restriction_type(self, client):
        """
            A single childtype allowed
        """
        registry = self.registry

        class DummyNode(object):
            def content(self):
                class DummyContent(object):
                    meta_type = 'dummycontent'

                class DummyType(Spoke):
                    model = DummyContent
                    children = (Type1Type,)

                    @classmethod
                    def name(self):
                        return DummyContent.meta_type

                registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), "view")
        assert toolbar.children() == [dict(name="type1")]

    def test_restriction_none(self, client):
        """
            No children at all allowed
        """
        registry = self.registry

        class DummyNode(object):
            def content(self):
                class DummyContent(object):
                    meta_type = 'dummycontent'

                class DummyType(Spoke):
                    model = DummyContent
                    children = ()

                    @classmethod
                    def name(self):
                        return DummyContent.meta_type

                registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), "view")
        assert toolbar.children() == []
        assert not toolbar.show_create()

    def test_show_create_status_create(self, client):
        node = Node.root()
        toolbar = Toolbar(node, "create")
        assert not toolbar.show_create()

