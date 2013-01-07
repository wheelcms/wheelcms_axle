from wheelcms_axle.main import MainHandler
from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1

from two.ol.base import NotFound
import pytest

from twotest.util import create_request

class MainHandlerTestable(MainHandler):
    """ intercept template() call to avoid rendering """
    def template(self, path):
        return dict(path=path, context=self.context)


class TestMainHandler(object):
    def test_coerce_instance(self, client):
        """ coerce a dict holding an instance path """
        root = Node.root()
        a = root.add("a")
        res = MainHandler.coerce(dict(instance="a"))
        assert 'instance' in res
        assert res['instance'] == a
        assert 'parent' not in res

    def test_coerce_parent(self, client):
        """ coerce a dict holding an parent path """
        root = Node.root()
        a = root.add("a")
        res = MainHandler.coerce(dict(parent="a"))
        assert 'parent' in res
        assert res['parent'] == a
        assert 'instance' not in res

    def test_coerce_instance_parent(self, client):
        """ coerce a dict holding both instance and parent """
        root = Node.root()
        a = root.add("a")
        b = a.add("b")
        res = MainHandler.coerce(dict(instance="b", parent="a"))
        assert 'instance' in res
        assert 'parent' in res
        assert res['instance'] == b
        assert res['parent'] == a

    def test_coerce_instance_notfound(self, client):
        """ coerce a non-existing path for instance """
        pytest.raises(NotFound, MainHandler.coerce, dict(instance="a"))

    def test_coerce_parent_notfound(self, client):
        """ coerce a non-existing path for parent """
        pytest.raises(NotFound, MainHandler.coerce, dict(parent="a"))

    def test_create_get_root(self, client):
        """ test create on root - get """
        root = Node.root()
        Type1(node=root).save()
        request = create_request("GET", "/", data=dict(type="type1"))
        handler = MainHandlerTestable(request=request, instance=root)
        create = handler.create()
        assert create['path'] == "wheelcms_axle/create.html"
        assert 'form' in create['context']

    def test_update_root(self, client):
        """ test /edit """
        root = Node.root()
        Type1(node=root).save()
        request = create_request("GET", "/edit")
        instance = MainHandlerTestable.coerce(dict(instance=""))
        handler = MainHandlerTestable(request=request, instance=instance)
        update = handler.update()
        assert update['path'] == "wheelcms_axle/update.html"
        assert 'form' in update['context']

    def test_create_attach(self, client):
        pytest.skip("Test attaching content in stead of creating")


class TestBreadcrumb(object):
    """ test breadcrumb generation by handler """

    def test_unattached_root(self, client):
        root = Node.root()
        request = create_request("GET", "/edit")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Unattached node /", '')]

    def test_attached_root(self, client):
        """ A root node with content attached """
        root = Node.root()
        Type1(node=root, title="Root").save()
        request = create_request("GET", "/")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Root", '')]

    def test_sub(self, client):
        """ a child with content under the root """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child)
        assert handler.breadcrumb() == [("Root", '/'), ("Child", "")]

        ## root should ignore child
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Root", '')]

    def test_subsub(self, client):
        """ a child with content under the root """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        child2 = child.add("child2")
        Type1(node=child2, title="Child2").save()
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child2)
        assert handler.breadcrumb() == [("Root", '/'), ("Child", "/child"),
                                        ("Child2", "")]

        ## root should ignore child
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Root", '')]

    def test_subsub_unattached(self, client):
        """ a child with content under the root, lowest child unattached """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        child2 = child.add("child2")
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child2)
        assert handler.breadcrumb() == [("Root", '/'), ("Child", "/child"),
                                        ("Unattached node /child/child2", "")]

    def test_parent_instance(self, client):
        """ handler initialized with a parent but no instance. Should
            mean edit mode, but for now assume custom breadcrumb context """
        root = Node.root()
        Type1(node=root, title="Root").save()
        request = create_request("GET", "/")
        handler = MainHandlerTestable(request=request, kw=dict(parent=root))

        assert handler.breadcrumb() == []


    def test_subsub_operation(self, client):
        """ a child with content under the root """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        child2 = child.add("child2")
        Type1(node=child2, title="Child2").save()
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child2)
        assert handler.breadcrumb(operation="Edit") == [
            ("Root", '/'), ("Child", "/child"),
            ("Child2", "/child/child2"), ("Edit", "")]

    def test_create(self, client):
        """ create should override and add Create operation crumb """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = create_request("GET", "/child/create")

        handler = MainHandlerTestable(request=request, instance=child)
        context = handler.create(type="type1")['context']
        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [('Root', '/'), ('Child', '/child'),
                                         ('Create', '')]

    def test_update(self, client):
        """ update should override and add Update operation crumb """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = create_request("GET", "/child/create")

        handler = MainHandlerTestable(request=request, instance=child)
        context = handler.update()['context']
        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [('Root', '/'), ('Child', '/child'),
                                         ('Edit', '')]
