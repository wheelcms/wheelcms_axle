# *-* encoding: utf-8
from wheelcms_axle.main import MainHandler
from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1, Type1Type

from two.ol.base import NotFound, Redirect, handler
import pytest

from twotest.util import create_request
from django.contrib.auth.models import User

class MainHandlerTestable(MainHandler):
    """ intercept template() call to avoid rendering """
    def render_template(self, template, **context):
        return dict(template=template, context=context)

    def template(self, path):
        return dict(path=path, context=self.context)

    def handle_reserved(self):
        """ should result in 'reserved' being a reserved kw """

    def foobar(self):
        """ should not result in a reserved keyword """

    @handler
    def decorated(self):
        pass


def superuser_request(path, method="GET", **data):
    superuser, _ = User.objects.get_or_create(username="superuser",
                                                   is_superuser=True)
    request = create_request(method, path, data=data)
    request.user = superuser
    return request

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
        request = superuser_request("/", type=Type1.get_name())
        handler = MainHandlerTestable(request=request, instance=root)
        create = handler.create()
        assert create['path'] == "wheelcms_axle/create.html"
        assert 'form' in create['context']

    def test_update_root(self, client):
        """ test /edit """
        root = Node.root()
        Type1(node=root).save()
        request = superuser_request("/edit", method="POST", type=Type1.get_name())
        instance = MainHandlerTestable.coerce(dict(instance=""))
        handler = MainHandlerTestable(request=request, instance=instance)
        update = handler.update()
        assert update['path'] == "wheelcms_axle/update.html"
        assert 'form' in update['context']

    def test_create_attach_get(self, client):
        """ get the form for attaching content """
        root = Node.root()
        Type1(node=root).save()
        request = superuser_request("/", type=Type1.get_name())
        handler = MainHandlerTestable(request=request, instance=root)
        create = handler.create(type=Type1.get_name(), attach=True)
        assert create['path'] == "wheelcms_axle/create.html"
        assert 'form' in create['context']

    def test_create_attach_post(self, client):
        """ post the form for attaching content """
        request = superuser_request("/create", method="POST",
                                      title="Test")
        root = Node.root()
        handler = MainHandler(request=request, post=True,
                              instance=dict(instance=root))
        pytest.raises(Redirect, handler.create, type=Type1.get_name(), attach=True)

        root = Node.root()
        # pytest.set_trace()
        assert root.content().title == "Test"

    def test_attached_form(self, client):
        """ The form when attaching should not contain a slug field since it
            will be attached to an existing node """
        root = Node.root()
        Type1(node=root).save()
        request = superuser_request("/")
        handler = MainHandlerTestable(request=request, instance=root)
        create = handler.create(type=Type1.get_name(), attach=True)

        form = create['context']['form']
        assert 'slug' not in form.fields

    def test_create_post(self, client):
        request = superuser_request("/create", method="POST",
                                      title="Test",
                                      slug="test")
        root = Node.root()
        handler = MainHandler(request=request, post=True,
                              instance=dict(instance=root))
        pytest.raises(Redirect, handler.create, type=Type1.get_name())

        node = Node.get("/test")
        assert node.content().title == "Test"

    def test_update_post(self, client):
        root = Node.root()
        Type1(node=root, title="Hello").save()
        request = superuser_request("/edit", method="POST",
                                      title="Test",
                                      slug="")
        root = Node.root()
        handler = MainHandler(request=request, post=True, instance=root)
        pytest.raises(Redirect, handler.update)

        root = Node.root()
        assert root.content().title == "Test"

    def test_reserved_default(self, client):
        reserved = MainHandlerTestable.reserved()
        assert 'create' in reserved
        assert 'list' in reserved
        assert 'update' in reserved

    def test_reserved_handle_explicit(self, client):
        reserved = MainHandlerTestable.reserved()
        assert 'reserved' in reserved
        assert 'foobar' not in reserved

    def test_reserved_decorator(self, client):
        reserved = MainHandlerTestable.reserved()
        assert 'decorated' in reserved

    def test_create_post_unicode(self, client):
        """ issue #693 - unicode enoding issue """
        request = superuser_request("/create", method="POST",
                           title=u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!",
                           slug="test")
        root = Node.root()
        handler = MainHandler(request=request, post=True,
                              instance=dict(instance=root))
        pytest.raises(Redirect, handler.create, type=Type1.get_name())

        node = Node.get("/test")
        assert node.content().title == u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"

    def test_update_post_unicode(self, client):
        """ update content with unicode with new unicode title """
        root = Node.root()
        Type1(node=root, title=u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!").save()
        request = superuser_request("/edit", method="POST",
                                      title="TTesting «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!",
                                      slug="")
        root = Node.root()
        handler = MainHandler(request=request, post=True, instance=root)
        pytest.raises(Redirect, handler.update)

        root = Node.root()
        assert root.content().title == u"TTesting «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"

class TestBreadcrumb(object):
    """ test breadcrumb generation by handler """

    def test_unattached_root(self, client):
        root = Node.root()
        request = create_request("GET", "/edit")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Unattached rootnode", '')]

    def test_attached_root(self, client):
        """ A root node with content attached. Its name should not be
            its title but 'Home' """
        root = Node.root()
        Type1(node=root, title="The rootnode of this site").save()
        request = create_request("GET", "/")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Home", '')]

    def test_sub(self, client):
        """ a child with content under the root """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child)
        assert handler.breadcrumb() == [("Home", root.get_absolute_url()),
                                        ("Child", "")]

        ## root should ignore child
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Home", '')]

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
        assert handler.breadcrumb() == [("Home", root.get_absolute_url()),
                                        ("Child", child.get_absolute_url()),
                                        ("Child2", "")]

        ## root should ignore child
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Home", '')]

    def test_subsub_unattached(self, client):
        """ a child with content under the root, lowest child unattached """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        child2 = child.add("child2")
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child2)
        assert handler.breadcrumb() == [("Home", root.get_absolute_url()),
                                        ("Child", child.get_absolute_url()),
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
            ("Home", root.get_absolute_url()),
            ("Child", child.get_absolute_url()),
            ("Child2", child2.get_absolute_url()), ("Edit", "")]

    def test_create_get(self, client):
        """ create should override and add Create operation crumb """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = superuser_request("/child/create")

        handler = MainHandlerTestable(request=request, instance=child)
        context = handler.create(type=Type1.get_name())['context']
        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [('Home', root.get_absolute_url()),
                                         ('Child', child.get_absolute_url()),
                                         ('Create "%s"' % Type1Type.title, '')]

    def test_update(self, client):
        """ update should override and add Update operation crumb """
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = superuser_request("/child/create")

        handler = MainHandlerTestable(request=request, instance=child)
        context = handler.update()['context']
        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [
                   ('Home', root.get_absolute_url()),
                   ('Child', child.get_absolute_url()),
                   ('Edit "%s" (%s)' % (child.content().title,
                                        Type1Type.title), '')]

class TestActions(object):
    """ test cut/copy/paste/delete, reorder and other actions """
    def test_cut_action(self, client):
        """ cut should clear the copy clipboard and add to the cut clipboard """
        root = Node.root()
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="cut",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])

        ## pretend there's still something in the buffer
        request.session['clipboard_copy'] = [t1.node.tree_path]

        handler = MainHandlerTestable(request=request, instance=root, post=True)

        pytest.raises(Redirect, handler.handle_contents_actions_cutcopypaste)

        assert request.session['clipboard_copy'] == []
        assert set(request.session['clipboard_cut']) == \
               set((t1.node.tree_path, t2.node.tree_path))

    def test_copy_action(self, client):
        """ copy should clear the cut clipboard and add to the copy clipboard """
        root = Node.root()
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="copy",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])

        ## pretend there's still something in the buffer
        request.session['clipboard_cut'] = [t1.node.tree_path]

        handler = MainHandlerTestable(request=request, instance=root, post=True)

        pytest.raises(Redirect, handler.handle_contents_actions_cutcopypaste)

        assert request.session['clipboard_cut'] == []
        assert set(request.session['clipboard_copy']) == \
               set((t1.node.tree_path, t2.node.tree_path))

    def test_paste_copy_action(self, client):
        """ paste after copy means duplicating content, can be in same
            node """
        root = Node.root()
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="paste",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_copy'] = [t1.node.tree_path]

        handler = MainHandlerTestable(request=request, instance=root, post=True)

        pytest.raises(Redirect, handler.handle_contents_actions_cutcopypaste)
        assert len(root.children()) == 3
        assert list(root.children())[-1].content().title == "t1"

    def test_paste_cut_action(self, client):
        """ paste after cut moves content, must be in different node to have
            any effect """
        root = Node.root()
        target = root.add("target")

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="paste",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_cut'] = [t2.node.tree_path, t1.node.tree_path]

        handler = MainHandlerTestable(request=request, instance=target,
                                      post=True)

        pytest.raises(Redirect, handler.handle_contents_actions_cutcopypaste)
        assert len(target.children()) == 2
        assert set(x.content().title for x in target.children()) == \
               set(('t1', 't2'))
        assert len(root.children()) == 1
        assert root.child('target')

    def test_delete_action(self, client):
        root = Node.root()

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_delete",
                                    method="POST",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_cut'] = [t2.node.tree_path, t1.node.tree_path]

        handler = MainHandlerTestable(request=request, instance=root,
                                      post=True)

        pytest.raises(Redirect, handler.handle_contents_actions_delete)

        assert len(root.children()) == 0
        assert Type1.objects.all().count() == 0


    def test_reorder_before(self, client):
        """ move a node to the top """
        root = Node.root()
        n1 = root.add("n1")
        n2 = root.add("n2")
        n3 = root.add("n3")

        request = superuser_request("/reorder",
                                    method="POST",
                                    rel="before",
                                    target=n3.tree_path,
                                    ref=n1.tree_path)

        handler = MainHandlerTestable(request=request, instance=root, post=True)

        res = handler.handle_reorder()

        n1 = Node.objects.get(pk=n1.pk)
        n2 = Node.objects.get(pk=n2.pk)
        n3 = Node.objects.get(pk=n3.pk)

        assert n3.position < n1.position
        assert n1.position < n2.position

    def test_reorder_after(self, client):
        """ move a node to the bottom """
        root = Node.root()
        n1 = root.add("n1")
        n2 = root.add("n2")
        n3 = root.add("n3")

        request = superuser_request("/reorder",
                                    method="POST",
                                    rel="after",
                                    target=n1.tree_path,
                                    ref=n3.tree_path)

        handler = MainHandlerTestable(request=request, instance=root, post=True)

        res = handler.handle_reorder()

        n1 = Node.objects.get(pk=n1.pk)
        n2 = Node.objects.get(pk=n2.pk)
        n3 = Node.objects.get(pk=n3.pk)

        assert n1.position > n3.position
        assert n3.position > n2.position

class TestTranslations(object):
    def test_translated(self, client):
        """ /a can point to either dutch or english content on different
            nodes """
        root = Node.root()
        n1 = root.add(langslugs=dict(nl="a", en="b"))
        n2 = root.add(langslugs=dict(en="a", nl="b"))

        from django.utils import translation

        translation.activate('nl')
        res = MainHandler.coerce(dict(instance="a"))
        assert res['instance'] == n1

        translation.activate('en')
        res = MainHandler.coerce(dict(instance="a"))
        assert res['instance'] == n2

