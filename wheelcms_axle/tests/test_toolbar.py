"""
    Test the toolbar class
"""
from django.contrib.auth.models import User

from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry
from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle.tests.models import Type1, Type1Type, Type2Type, TestTypeRegistry

from wheelcms_axle.spoke import Spoke

from .test_handler import superuser_request
from twotest.util import create_request

class BaseToolbarTest(object):
    def setup(self):
        self.registry = TestTypeRegistry()
        type_registry.set(self.registry)
        self.registry.register(Type1Type)
        self.registry.register(Type2Type)


class TestToolbar(BaseToolbarTest):
    """
        Test toolbar child restrictions, context buttons
    """
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

    def test_primary(self, client):
        """ a type with primary should behave differently """

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
                    children = (Type1Type, Type2Type)
                    primary = Type1Type

                    @classmethod
                    def name(self):
                        return DummyContent.get_name()

                registry.register(DummyType)

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

from django.utils import translation
from django.conf import settings

class TestTranslations(BaseToolbarTest):
    def setup(self):
        super(TestTranslations, self).setup()

        settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))
        settings.FALLBACK = False

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
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=nl')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=fr')

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
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=nl&rest=edit')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=fr&rest=edit')

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
        assert translations['translated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=nl&rest=list')
        assert translations['untranslated'][0]['id'] == 'fr'
        assert translations['untranslated'][0]['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=fr&rest=list')

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
            assert ut['action_url'].endswith('switch_admin_language?path='+n.tree_path + '&language=' + l + '&rest=' + urllib2.quote('create?type=sometype'))
