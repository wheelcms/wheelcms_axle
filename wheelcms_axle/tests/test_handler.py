# *-* encoding: utf-8
import mock

from django.utils import translation
from django.http import Http404

from wheelcms_axle.main import MainHandler
from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1, Type1Type
from wheelcms_axle import locale


from two.ol.base import NotFound, Redirect, handler
import pytest

from twotest.util import create_request
from django.contrib.auth.models import User
from django.template import RequestContext

from .fixtures import root

class MainHandlerTestable(MainHandler):
    """ intercept template() call to avoid rendering """
    def render_template(self, template, **context):
        return dict(template=template, context=context)

    def template(self, path, **kw):
        return dict(path=path, context=self.context, kw=kw)

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

@pytest.mark.usefixtures("localtyperegistry", "active_language")
class TestMainHandler(object):
    type = Type1Type

    def test_dispatch_existing(self, client, root):
        """ coerce a dict holding an instance path """
        a = root.add("a")

        h = MainHandlerTestable()
        request = superuser_request("/a")
        res = h.dispatch(request, nodepath="/a")
        assert h.instance == a

    def test_dispatch_notfound(self, client):
        """ coerce a non-existing path for instance """
        request = superuser_request("/a")
        h = MainHandlerTestable()
        with pytest.raises(Http404):
            res = h.dispatch(request, nodepath="/a")
            assert h.instance is None


    def test_update_get_root(self, client, root):
        """ test update on root - get """
        Type1(node=root).save()
        request = superuser_request("/edit", type=Type1.get_name())
        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="", handlerpath="edit")
        assert res['path'] == "wheelcms_axle/update.html"
        assert 'form' in res['context']

    def test_update_root(self, client, root):
        """ test /edit """
        Type1(node=root).save()
        request = superuser_request("/edit", method="POST", type=Type1.get_name())
        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="", handlerpath="edit")
        assert res['path'] == "wheelcms_axle/update.html"
        assert 'form' in res['context']

    def test_create_attach_get(self, client, root):
        """ get the form for attaching content """
        Type1(node=root).save()
        request = superuser_request("/", type=Type1.get_name(), attach=True)
        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="", handlerpath="create")

        assert res['path'] == "wheelcms_axle/create.html"
        assert 'form' in res['context']

    def test_create_attach_post(self, client, root):
        """ post the form for attaching content """
        request = superuser_request("/create", method="POST",
                                      title="Test", language="en",
                                      type=Type1.get_name(), attach=True)
        view = MainHandlerTestable()

        res = view.dispatch(request, nodepath="", handlerpath="create")
        assert res.status_code == 302

        assert root.content().title == "Test"

    def test_attached_form(self, client, root):
        """ The form when attaching should not contain a slug field since it
            will be attached to an existing node """
        Type1(node=root).save()
        request = superuser_request("/", type=Type1.get_name(), attach=True)
        handler = MainHandlerTestable()

        res = handler.dispatch(request, nodepath="", handlerpath="create")

        form = res['context']['form']
        assert 'slug' not in form.fields

    def test_create_post(self, client, root):
        request = superuser_request("/create", method="POST",
                                      title="Test",
                                      slug="test",
                                      language="en",
                                      type=Type1.get_name())
        handler = MainHandlerTestable()

        res = handler.dispatch(request, nodepath="", handlerpath="create")
        assert res.status_code == 302


        node = Node.get("/test")
        assert node.content().title == "Test"

    def test_update_post(self, client, root):
        Type1(node=root, title="Hello").save()
        request = superuser_request("/edit", method="POST",
                                      title="Test",
                                      slug="",
                                      language="en")
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="edit")
        assert res.status_code == 302

        assert root.content().title == "Test"

    def test_create_translation_root_get(self, client, root):
        """ test case where root has content but current language
            is not translated """
        Type1(node=root, title="Hello", language="en").save()
        request = superuser_request("/edit", method="GET",
                                    language="nl")
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="edit")

        assert 'slug' not in res['context']['form'].fields

    def test_create_translation_root_post(self, client, root):
        """ test case where root has content but current language
            is not translated """
        Type1(node=root, title="Hello", language="en").save()
        request = superuser_request("/edit", method="POST",
                                    title="hello",
                                    language="nl")
        locale.activate_content_language('nl')

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="edit")

        assert res.status_code == 302
        assert root.content(language='nl')
        assert root.content(language='en')
        assert root.content(language='nl') != root.content(language='en')

    def test_create_translation_content_get(self, client, root):
        """ test case where root has content but current language
            is not translated """
        node = root.add("content")
        Type1(node=node, title="Hello", language="en").save()
        request = superuser_request("/edit", method="GET",
                                    language="nl")
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="/content", handlerpath="edit")

        assert 'slug' in res['context']['form'].fields

    def test_create_translation_content_post(self, client, root):
        """ test case where root has content but current language
            is not translated """
        node = root.add("content")
        Type1(node=node, title="Hello", language="en").save()
        request = superuser_request("/edit", method="POST",
                                    title="hello",
                                    language="nl")
        locale.activate_content_language('nl')

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="content", handlerpath="edit")

        assert res.status_code == 302

        assert node.content(language='nl')
        assert node.content(language='en')
        assert node.content(language='nl') != node.content(language='en')

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

    def test_create_post_unicode(self, client, root):
        """ issue #693 - unicode enoding issue """
        request = superuser_request("/create", method="POST",
                           title=u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!",
                           slug="test",
                           language="en",
                           type=Type1.get_name())
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="create")

        assert res.status_code == 302
        node = Node.get("/test")
        assert node.content().title == u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"

    def test_update_post_unicode(self, client, root):
        """ update content with unicode with new unicode title """
        Type1(node=root, title=u"Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!").save()
        request = superuser_request("/edit", method="POST",
                                      title="TTesting «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!",
                                      slug="",
                                      language="en")
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="edit")

        assert res.status_code == 302
        assert root.content().title == u"TTesting «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!"

    def test_change_slug_inuse(self, client, root):
        Type1(node=root.add("inuse"), title="InUse").save()
        other = Type1(node=root.add("other"), title="Other").save()
        request = superuser_request("/other/update", method="POST",
                                    title="Other", slug="inuse",
                                    language="en")

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="/other", handlerpath="edit")

        form = res['context']['form']
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_change_slug_available(self, client, root):
        Type1(node=root.add("inuse"), title="InUse").save()
        other = Type1(node=root.add("other"), title="Other").save()
        request = superuser_request("/other/update", method="POST",
                                    title="Other", slug="inuse2",
                                    language="en")

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="/other", handlerpath="edit")

        assert res.status_code == 302

        form = handler.context['form']
        assert form.is_valid()

    def test_handle_list(self, client, root):
        """ issue #799 - no raw node is returned for getting slug or path """
        t = Type1(node=root.add("attached"), title="Attached").save()
        u = root.add("unattached")

        request = superuser_request("/list", method="GET")

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="list")

        path = res['path']
        context = res['context']

        assert path == "wheelcms_axle/contents.html"
        assert 'children' in context
        children = context['children']
        assert len(children) == 2

        assert children[0]['active'] == t
        assert children[1]['active'] is None
        # fails because children[1]['node'] is language-wrapped
        # assert children[1]['node'] == u
        assert children[1]['node'].path == u.path


@pytest.mark.usefixtures("localtyperegistry")
class TestBreadcrumb(object):
    """ test breadcrumb generation by handler """
    type = Type1Type

    def test_unattached_root(self, client, root):
        request = create_request("GET", "/edit")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Unattached rootnode", '')]

    def test_attached_root(self, client, root):
        """ A root node with content attached. Its name should not be
            its title but 'Home' """
        Type1(node=root, title="The rootnode of this site").save()
        request = create_request("GET", "/")
        handler = MainHandlerTestable(request=request, instance=root)
        assert handler.breadcrumb() == [("Home", '')]

    def test_sub(self, client, root):
        """ a child with content under the root """
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

    def test_subsub(self, client, root):
        """ a child with content under the root """
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

    def test_subsub_unattached(self, client, root):
        """ a child with content under the root, lowest child unattached """
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        child2 = child.add("child2")
        request = create_request("GET", "/")

        handler = MainHandlerTestable(request=request, instance=child2)
        assert handler.breadcrumb() == [("Home", root.get_absolute_url()),
                                        ("Child", child.get_absolute_url()),
                                        ("Unattached node /child/child2", "")]

    def test_subsub_operation(self, client, root):
        """ a child with content under the root """
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

    def test_create_get(self, client, root):
        """ create should override and add Create operation crumb """
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = superuser_request("/child/create", type=Type1.get_name())

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath=child.path, handlerpath="create")

        context = res['context']

        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [('Home', root.get_absolute_url()),
                                         ('Child', child.get_absolute_url()),
                                         ('Create "%s"' % Type1Type.title, '')]

    def test_update(self, client, root):
        """ update should override and add Update operation crumb """
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = superuser_request("/child/edit", method="GET")

        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath=child.path, handlerpath="edit")
        context = res['context']

        assert 'breadcrumb' in context
        assert context['breadcrumb'] == [
                   ('Home', root.get_absolute_url()),
                   ('Child', child.get_absolute_url()),
                   ('Edit "%s" (%s)' % (child.content().title,
                                        Type1Type.title), '')]


@pytest.mark.usefixtures("localtyperegistry")
class TestActions(object):
    """ test cut/copy/paste/delete, reorder and other actions """
    type = Type1Type

    def test_cut_action(self, client, root):
        """ cut should clear the copy clipboard and add to the cut clipboard """
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="cut",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])

        ## pretend there's still something in the buffer
        request.session['clipboard_copy'] = [t1.node.tree_path]

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="",
                            handlerpath="contents_actions_cutcopypaste",
                            action="cut")

        assert res.status_code == 302  # redirect
        assert res['location'] == root.get_absolute_url() + 'list'
        assert request.session['clipboard_copy'] == []
        assert set(request.session['clipboard_cut']) == \
               set((t1.node.tree_path, t2.node.tree_path))

    def test_copy_action(self, client, root):
        """ copy should clear the cut clipboard and add to the copy clipboard """
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="copy",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])

        ## pretend there's still something in the buffer
        request.session['clipboard_cut'] = [t1.node.tree_path]

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="",
                            handlerpath="contents_actions_cutcopypaste",
                            action="copy")

        assert res.status_code == 302  # redirect
        assert res['location'] == root.get_absolute_url() + 'list'
        assert request.session['clipboard_cut'] == []
        assert set(request.session['clipboard_copy']) == \
               set((t1.node.tree_path, t2.node.tree_path))

    def test_paste_copy_action(self, client, root):
        """ paste after copy means duplicating content, can be in same
            node """
        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="paste",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_copy'] = [t1.node.tree_path]

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="",
                            handlerpath="contents_actions_cutcopypaste",
                            action="paste")

        assert res.status_code == 302  # redirect
        assert res['location'] == root.get_absolute_url() + 'list'

        assert len(root.children()) == 3
        assert list(root.children())[-1].content().title == "t1"

    def test_paste_cut_action(self, client, root):
        """ paste after cut moves content, must be in different node to have
            any effect """
        target = root.add("target")

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_cutcopypaste",
                                    method="POST", action="paste",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_cut'] = [t2.node.tree_path, t1.node.tree_path]

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="/target",
                            handlerpath="contents_actions_cutcopypaste",
                            action="paste")

        assert res.status_code == 302  # redirect
        assert res['location'] == target.get_absolute_url() + 'list'

        assert len(target.children()) == 2
        assert set(x.content().title for x in target.children()) == \
               set(('t1', 't2'))
        assert len(root.children()) == 1
        assert root.child('target')

    def test_delete_action(self, client, root):

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()


        request = superuser_request("/contents_actions_delete",
                                    method="POST",
                                    selection=[t1.node.tree_path,
                                               t2.node.tree_path])
        request.session['clipboard_cut'] = [t2.node.tree_path, t1.node.tree_path]

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="",
                            handlerpath="contents_actions_delete")

        assert res.status_code == 302  # redirect
        assert res['location'] == root.get_absolute_url() + 'list'

        assert len(root.children()) == 0
        assert Type1.objects.all().count() == 0


    def test_reorder_before(self, client, root):
        """ move a node to the top """
        n1 = root.add("n1")
        n2 = root.add("n2")
        n3 = root.add("n3")

        request = superuser_request("/reorder",
                                    method="POST",
                                    rel="before",
                                    target=n3.tree_path,
                                    ref=n1.tree_path)

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="", handlerpath="reorder")

        n1 = Node.objects.get(pk=n1.pk)
        n2 = Node.objects.get(pk=n2.pk)
        n3 = Node.objects.get(pk=n3.pk)

        assert n3.position < n1.position
        assert n1.position < n2.position

    def test_reorder_after(self, client, root):
        """ move a node to the bottom """
        n1 = root.add("n1")
        n2 = root.add("n2")
        n3 = root.add("n3")

        request = superuser_request("/reorder",
                                    method="POST",
                                    rel="after",
                                    target=n1.tree_path,
                                    ref=n3.tree_path)

        view = MainHandlerTestable()
        res = view.dispatch(request, nodepath="", handlerpath="reorder")

        n1 = Node.objects.get(pk=n1.pk)
        n2 = Node.objects.get(pk=n2.pk)
        n3 = Node.objects.get(pk=n3.pk)

        assert n1.position > n3.position
        assert n3.position > n2.position

from .fixtures import multilang_ENNL, active_language

@pytest.mark.usefixtures("multilang_ENNL", "active_language",
                         "localtyperegistry")
class TestTranslations(object):
    type = Type1Type

    def test_translated(self, client, root):
        """ /a can point to either dutch or english content on different
            nodes """
        n1 = root.add(langslugs=dict(nl="a", en="b"))
        n2 = root.add(langslugs=dict(en="a", nl="b"))


        translation.activate('nl')
        res = MainHandler.resolve("a")
        assert res == n1

        translation.activate('en')
        res = MainHandler.resolve("a")
        assert res == n2

    def test_create_translation_get(self, client, root):
        """
            Creating a translation on existing content is actually
            an update operation (it's handled by the update() method.
            Test the GET of the translation form
        """
        Type1(node=root, language="en").save()
        request = superuser_request("/", method="GET",
                                    type=Type1.get_name())
        translation.activate('nl')

        view = MainHandlerTestable()
        update = view.dispatch(request, nodepath="", handlerpath="edit")


        assert update['path'] == "wheelcms_axle/update.html"
        assert 'form' in update['context']
        f = update['context']['form']

        assert f.initial['language'] == 'nl'

    def test_create_translation_post(self, client, root):
        """
            Creating a translation on existing content is actually
            an update operation (it's handled by the update() method.
            Test the POST of the form, the actual creation of the
            translation
        """
        Type1(node=root, language="en").save()
        request = superuser_request("/edit", method="POST",
                                    type=Type1.get_name(),
                                    title="Translation NL",
                                    language="nl")
        translation.activate('nl')

        view = MainHandlerTestable()
        update = view.dispatch(request, nodepath="", handlerpath="edit")

        assert update.status_code == 302  # redirect

        translated = root.content(language="nl")
        assert translated is not None
        assert translated.title == "Translation NL"
        assert translated.owner == request.user

        # verify we've redirected back to the created content
        assert update['location'] == translated.get_absolute_url()

from .test_spoke import filedata, filedata2
from .models import TestImage, TestImageType

@pytest.mark.usefixtures("localtyperegistry")
class TestImageCreateUpdate(object):
    types = (Type1Type, TestImageType)

    def test_create_image(self, client, root):
        request = superuser_request("/create", method="POST",
                                      title="Test",
                                      slug="test",
                                      language="en",
                                      storage=filedata,
                                      type=TestImage.get_name())
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="", handlerpath="create")

        assert res.status_code == 302

        node = Node.get("/test")
        filedata.seek(0)
        assert node.content().storage.read() == filedata.read()

    def test_update_image(self, client, root):
        node = root.add("test")
        TestImage(node=node, title="image", storage=filedata).save()
        request = superuser_request("/test/edit", method="POST",
                                      title="Test",
                                      slug="",
                                      language="en",
                                      storage=filedata2)
        handler = MainHandlerTestable()
        res = handler.dispatch(request, nodepath="/test", handlerpath="edit")

        assert res.status_code == 302

        node = Node.get("/test")
        filedata2.seek(0)
        assert node.content().storage.read() == filedata2.read()
