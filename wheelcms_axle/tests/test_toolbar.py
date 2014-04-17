"""
    Test the toolbar class
"""
from django.contrib.auth.models import User

from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry
from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle.tests.models import Type1, Type1Type, Type2Type

from wheelcms_axle.spoke import Spoke

from .test_handler import superuser_request
from twotest.util import create_request

from .utils import DummyContent

import mock

import pytest

@pytest.mark.usefixtures("localtyperegistry")
class TestToolbar(object):
    """
        Test toolbar child restrictions, context buttons
    """
    types = (Type1Type, Type2Type)

    def allchildren(self, children):
        """ match against all registered children """
        return set(x['name'] for x in children) == \
               set(c.name() for c in type_registry.values())

    @mock.patch("wheelcms_axle.content.type_registry.values",
                return_value=(mock.Mock(), mock.Mock()))
    def test_unconnected(self, mocked_registry):
        """
            Test behaviour on unconnected node - allow
            creation of all types of sub content
        """
        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=None):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.show_create()
            assert self.allchildren(t.children())

    @mock.patch("wheelcms_axle.content.type_registry.values",
                return_value=(mock.Mock(), mock.Mock()))
    def test_connected_no_restrictions(self, mocked_registry):
        """
            A node with content without restrictions
        """
        class T(mock.Mock):
            primary = children = None
            def allowed_spokes(self):
                return type_registry.values()

        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=T):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.show_create()
            assert self.allchildren(t.children())

    def test_restriction_type(self):
        """
            A single childtype allowed
        """
        c = mock.Mock()
        class T(mock.Mock):
            primary = None
            children = (c,)
            def allowed_spokes(self):
                return (c,)

        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=T):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.show_create()
            children = t.children()
            assert len(children) == 1
            assert children[0]['name'] == c.name()
            assert children[0]['title'] == c.title
            assert children[0]['icon_path'] == c.full_type_icon_path()


    def test_restriction_none(self, client):
        """
            No children at all allowed
        """
        class DummyNode(object):
            def content(self):
                class DummyType(Spoke):
                    model = DummyContent
                    children = ()
                    add_to_index = False

                    @classmethod
                    def name(cls):
                        return DummyContent.get_name()

                type_registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), superuser_request("/"), "view")
        assert toolbar.children() == []
        assert not toolbar.show_create()

    def test_create_mode_buttons(self, client):
        """ verify that certain buttons are not shown in create mode """
        node = Node.root()
        content = Type1(node=node)
        content.save()
        toolbar = Toolbar(node, superuser_request("/"), "create")
        assert not toolbar.show_create()
        assert not toolbar.show_update()

    def test_update_mode_buttons(self, client):
        """ verify that certain buttons are not shown in update mode """
        node = Node.root()
        content = Type1(node=node)
        content.save()
        toolbar = Toolbar(node, superuser_request("/"), "update")
        assert not toolbar.show_create()
        assert not toolbar.show_update()

    def test_no_implicit_unattached(self, client):
        """ An unattached node cannot restrict its children but
            should still not allow creation of non-implicit_add
            types """


        class DummyType(Spoke):
            model = DummyContent
            children = ()
            implicit_add = False
            add_to_index = False

            @classmethod
            def title(cls):
                return ''

        type_registry.register(DummyType)


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

    def test_primary(self, client):
        """ a type with primary should behave differently """


        class DummyNode(object):
            def content(self):
                class DummyType(Spoke):
                    model = DummyContent
                    children = (Type1Type, Type2Type)
                    primary = Type1Type
                    add_to_index = False

                    @classmethod
                    def name(cls):
                        return cls.model.get_name()

                type_registry.register(DummyType)

                return DummyContent()

        toolbar = Toolbar(DummyNode(), superuser_request("/"), "view")
        children = toolbar.children()
        assert len(children) == 1
        assert children[0]['name'] == Type2Type.name()
        assert children[0]['title'] == Type2Type.title
        assert children[0]['icon_path'] == Type2Type.full_type_icon_path()

        primary = toolbar.primary()
        assert primary
        assert primary['name'] == Type1Type.name()
        assert primary['title'] == Type1Type.title
        assert primary['icon_path'] == Type1Type.full_type_icon_path()

    def test_primary_unattached(self, client):
        """ an unattached node has no primary content """
        toolbar = Toolbar(Node.root(), superuser_request("/"), "view")
        assert toolbar.primary() is None

    def test_clipboard_empty(self, client):
        toolbar = Toolbar(Node.root(), superuser_request("/"), "view")
        clipboard = toolbar.clipboard()
        assert clipboard['count'] == 0
        assert not clipboard['copy']
        assert not clipboard['cut']
        assert clipboard['items'] == []

    def test_clipboard_cut(self, client):
        root = Node.root()

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()

        request = create_request("GET", "/")
        request.session['clipboard_cut'] = [t2.node.tree_path, t1.node.tree_path]

        toolbar = Toolbar(Node.root(), request, "view")
        clipboard = toolbar.clipboard()
        assert clipboard['count'] == 2
        assert not clipboard['copy']
        assert clipboard['cut']
        assert set(clipboard['items']) == set((t1, t2))

    def test_clipboard_copy(self, client):
        root = Node.root()

        t1 = Type1(node=root.add("t1"), title="t1").save()
        t2 = Type1(node=root.add("t2"), title="t2").save()

        request = create_request("GET", "/")
        request.session['clipboard_copy'] = [t2.node.tree_path, t1.node.tree_path]

        toolbar = Toolbar(Node.root(), request, "view")
        clipboard = toolbar.clipboard()
        assert clipboard['count'] == 2
        assert clipboard['copy']
        assert not clipboard['cut']
        assert set(clipboard['items']) == set((t1, t2))

    def test_single_child_empty(self):
        """ No allowed children means there's not "a single" child """
        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=mock.Mock(children=())):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.single_child() is None

    def test_single_child_multi(self):
        """ multiple allowed children means there's not "a single" child """
        c1 = mock.Mock()
        c2 = mock.Mock()

        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=mock.Mock(children=(c1, c2))):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.single_child() is None

    def test_single_child_single(self):
        """ only valid case where there's "a single" child """
        c1 = mock.Mock()
        with mock.patch("wheelcms_axle.toolbar.Toolbar.type",
                        return_value=mock.Mock(children=(c1,))):
            t = Toolbar(mock.Mock(), mock.Mock(), "view")
            assert t.single_child() is c1


from django.utils import translation
from .fixtures import multilang_ENNLFR, active_language

@pytest.mark.usefixtures("localtyperegistry", "multilang_ENNLFR", "active_language")
class TestTranslations(object):
    types = (Type1Type, Type2Type)

    def test_show_translate(self, client):
        root = Node.root()

        n = root.add(langslugs=dict(en="en", nl="nl", fr="fr"))
        t_nl = Type1(node=n, language="nl", title="NL").save()
        translation.activate("en")
        request = create_request("GET", "/")
        toolbar = Toolbar(n, request, "view")

        assert toolbar.show_translate()
        assert not toolbar.show_update()
        translation.activate("nl")
        assert not toolbar.show_translate()
        assert toolbar.show_update()


    def test_translations_view(self, client):
        root = Node.root()

        n = root.add(langslugs=dict(en="en", nl="nl", fr="fr"))
        t_nl = Type1(node=n, language="nl", title="NL").save()
        t_en = Type1(node=n, language="en", title="EN").save()


        request = create_request("GET", "/")

        translation.activate("en")
        toolbar = Toolbar(n, request, "view")
        translations = toolbar.translations()

        assert translations['active']['id'] == 'en'

        ## Do some matching magic using endswith to work around language / base prefixing.
        ## We're mosly interested in create/view/edit actions anyway
        assert translations['translated'][0]['id'] == "nl"
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=nl')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=fr')

    def test_translations_edit(self, client):
        root = Node.root()

        n = root.add(langslugs=dict(en="en", nl="nl", fr="fr"))
        t_nl = Type1(node=n, language="nl", title="NL").save()
        t_en = Type1(node=n, language="en", title="EN").save()


        request = create_request("GET", "/")

        translation.activate("en")
        toolbar = Toolbar(n, request, "update")
        translations = toolbar.translations()

        assert translations['active']['id'] == 'en'

        ## Do some matching magic using endswith to work around language / base prefixing.
        ## We're mosly interested in create/view/edit actions anyway
        assert translations['translated'][0]['id'] == "nl"
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=nl&rest=edit')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=fr&rest=edit')

    def test_translations_list(self, client):
        root = Node.root()

        n = root.add(langslugs=dict(en="en", nl="nl", fr="fr"))
        t_nl = Type1(node=n, language="nl", title="NL").save()
        t_en = Type1(node=n, language="en", title="EN").save()


        request = create_request("GET", "/")

        translation.activate("en")
        toolbar = Toolbar(n, request, "list")
        translations = toolbar.translations()

        assert translations['active']['id'] == 'en'

        ## Do some matching magic using endswith to work around language / base prefixing.
        ## We're mosly interested in create/view/edit actions anyway
        assert translations['translated'][0]['id'] == "nl"
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=nl&rest=list')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=fr&rest=list')

    def test_translations_create(self, client):
        root = Node.root()

        n = root.add(langslugs=dict(en="en", nl="nl", fr="fr"))
        t_nl = Type1(node=n, language="nl", title="NL").save()
        t_en = Type1(node=n, language="en", title="EN").save()


        request = create_request("GET", "/create", data=dict(type="sometype"))

        translation.activate("en")
        toolbar = Toolbar(n, request, "create")
        translations = toolbar.translations()

        assert translations['active']['id'] == 'en'

        import urllib2

        ## Do some matching magic using endswith to work around language / base prefixing.
        ## We're mosly interested in create/view/edit actions anyway
        assert len(translations['translated']) == 0
        assert len(translations['untranslated']) == 3  ## all languages incl 'any', active lang excluded

        for ut in translations['untranslated']:
            l = ut['id']
            assert l in ('nl', 'fr', 'en', 'any')
            assert ut['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&switchto=' + l + '&rest=' + urllib2.quote('create?type=sometype'))

from wheelcms_axle.toolbar import ButtonAction, PreviewAction, ToolbarAction
from .fixtures import toolbar_registry
import mock

@pytest.mark.usefixtures("localtyperegistry")
class TestToolbarActions(object):
    """
        Test custom / dynamic action button support
    """
    type = Type1Type

    def test_no_button_actions(self, client, root, toolbar_registry):
        """
            A node with content without restrictions
        """
        Type1Type.create(node=root).save()
        toolbar = Toolbar(root, superuser_request("/"), "view")

        assert len(toolbar.button_actions()) == 0

    def test_button_actions(self, client, root, toolbar_registry):
        """
            A node with content without restrictions
        """
        Type1Type.create(node=root).save()
        toolbar = Toolbar(root, superuser_request("/"), "view")

        toolbar_registry.register(ButtonAction("test"))
        assert len(toolbar.button_actions()) == 1

    def test_button_state_all(self, client, root, toolbar_registry):
        """ A toolbar action with states=() always shows """
        Type1Type.create(node=root).save()
        toolbar = Toolbar(root, superuser_request("/"), "edit")

        toolbar_registry.register(mock.Mock(type="button", states=()))
        assert len(toolbar.button_actions()) == 1

    def test_button_state_mismatch(self, client, root, toolbar_registry):
        """ If an explicit state is given, it must match with toolbar status
        """
        Type1Type.create(node=root).save()
        toolbar = Toolbar(root, superuser_request("/"), "edit")

        toolbar_registry.register(mock.Mock(type="button", states=("view",)))
        assert len(toolbar.button_actions()) == 0

    def test_button_state_any(self, client, root, toolbar_registry):
        """ If an explicit state is given, it must match with toolbar status
        """
        Type1Type.create(node=root).save()
        toolbar = Toolbar(root, superuser_request("/"), "edit")

        toolbar_registry.register(mock.Mock(type="button",
                                            states=("view", "edit")))
        assert len(toolbar.button_actions()) == 1

class BaseTestToolbarAction(object):
    """
        Test individual Toolbar Button actions
    """
    action = None

    def test_url(self):
        """ should not raise if no instance provided """
        assert self.action("test").url() or True

    def test_icon(self):
        assert self.action("test").name()

    def test_dont_show(self):
        action = self.action("test")

        action_with_toolbar = action.with_toolbar(mock.Mock(instance=None))
        assert not action_with_toolbar.show()

    def test_do_show(self):
        action = self.action("test")

        action_with_toolbar = action.with_toolbar(mock.Mock())
        assert action_with_toolbar.show()

class TestToolbarActionButtonAction(BaseTestToolbarAction):
    action = ToolbarAction

class TestToolbarActionButtonAction(BaseTestToolbarAction):
    action = ButtonAction

class TestToolbarActionPreviewction(BaseTestToolbarAction):
    action = PreviewAction

    def test_icon(self):
        assert self.action("test").icon()

    def test_attrs(self):
        assert 'target' in self.action("test").attrs()

    def test_url(self):
        """ verify get_absolute_url is invoked """
        m = mock.Mock(**{"instance.get_absolute_url.return_value": "/foo"})
        assert self.action("test").with_toolbar(m).url().startswith("/foo")
