"""
    Test the toolbar class
"""
from django.contrib.auth.models import User

from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry, TypeRegistry
from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle.tests.models import Type1, Type1Type, Type2Type, TestTypeRegistry

from wheelcms_axle.spoke import Spoke

from .test_handler import superuser_request
from twotest.util import create_request

class TestToolbar(object):
    """
        Test toolbar child restrictions, context buttons
    """
    def setup(self):
        self.registry = TestTypeRegistry()
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
        toolbar = Toolbar(root, superuser_request("/"), "view")
        assert toolbar.show_create()
        assert self.allchildren(toolbar.children())

    def test_connected_no_restrictions(self, client):
        """
            A node with content without restrictions
        """
        root = Node.root()
        content = Type1(node=root)
        content.save()
        toolbar = Toolbar(root, superuser_request("/"), "view")
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

                    @classmethod
                    def get_name(cls):
                        return "test." + cls.meta_type

                class DummyType(Spoke):
                    model = DummyContent
                    children = (Type1Type,)

                    @classmethod
                    def name(self):
                        return DummyContent.get_name()

                registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), superuser_request("/"), "view")
        children = toolbar.children()
        assert len(children) == 1
        assert children[0]['name'] == Type1Type.name()
        assert children[0]['title'] == Type1Type.title
        assert children[0]['icon_path'] == Type1Type.full_type_icon_path()

    def test_restriction_none(self, client):
        """
            No children at all allowed
        """
        registry = self.registry

        class DummyNode(object):
            def content(self):
                class DummyContent(object):
                    meta_type = 'dummycontent'

                    @classmethod
                    def get_name(cls):
                        return "test." + cls.meta_type

                class DummyType(Spoke):
                    model = DummyContent
                    children = ()

                    @classmethod
                    def name(self):
                        return DummyContent.get_name()

                registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), superuser_request("/"), "view")
        assert toolbar.children() == []
        assert not toolbar.show_create()

    def test_show_create_status_create(self, client):
        node = Node.root()
        toolbar = Toolbar(node, superuser_request("/"), "create")
        assert not toolbar.show_create()

    def test_no_implicit_unattached(self, client):
        """ An unattached node cannot restrict its children but
            should still not allow creation of non-implicit_add
            types """

        class DummyContent(object):
            meta_type = 'dummycontent'

            @classmethod
            def get_name(cls):
                return "test." + cls.meta_type

        class DummyType(Spoke):
            model = DummyContent
            children = ()
            implicit_add = False

            @classmethod
            def title(cls):
                return ''

        self.registry.register(DummyType)


        node = Node.root()
        toolbar = Toolbar(node, superuser_request("/"), "view")
        for c in toolbar.children():
            assert c['name'] != DummyType.name()

    def test_anon_no_settings(self, client):
        node = Node.root()
        toolbar = Toolbar(node, create_request("GET", "/"), "view")
        assert not toolbar.show_settings()

    def test_nosu_no_settings(self, client):
        user, _ = User.objects.get_or_create(username="user")
        request = create_request("GET", "/")
        request.user = user

        node = Node.root()
        toolbar = Toolbar(node, request, "view")
        assert not toolbar.show_settings()


