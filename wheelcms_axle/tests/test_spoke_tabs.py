import mock
import pytest
from drole.types import Permission
from wheelcms_axle.spoke import Spoke, tab
from wheelcms_axle.actions import action_registry


@pytest.mark.usefixtures("localactionregistry")
class TestSpokeTabs(object):
    def test_defaults(self):
        """ simple @action() syntax """
        f = mock.MagicMock(func_name="callme", tab=False, action=False)
        f = tab()(f)
        assert f.action
        assert f.tab
        assert f.tab_id == "callme"
        assert f.tab_label == "callme"
        assert f.permission is None

    def test_permission(self):
        """ @tab(id=xx, permission=xx) syntax """
        f = mock.MagicMock(func_name="callme", tab=False, action=False)
        f = tab(Permission("foo"))(f)

        assert f.action
        assert f.tab
        assert f.tab_id == "callme"
        assert f.tab_label == "callme"
        assert f.permission == Permission("foo")

    def test_arguments(self):
        """ @tab(id=xx, permission=xx) syntax """
        f = mock.MagicMock(tab=False, action=False)
        f = tab(id="foo", label="Bar", permission=Permission("foo"))(f)

        assert f.action
        assert f.tab
        assert f.tab_id == "foo"
        assert f.tab_label == "Bar"
        assert f.permission == Permission("foo")

    def test_default_label_to_id(self):
        """ @tab(id=xx) syntax """
        f = mock.MagicMock(func_name="callme", tab=False, action=False)
        f = tab(id="foo", permission=Permission("foo"))(f)

        assert f.action
        assert f.tab
        assert f.tab_id == "foo"
        assert f.tab_label == "foo"

    def test_basetab(self):
        """ No basetabs and no decorated tabs """
        class TestSpoke(Spoke):
            basetabs = ()

            auth = None  ## clear auth tab

        s = TestSpoke(mock.MagicMock(tab=False, action=False))

        assert s.tabs() == ()

    def test_basetab_action(self):
        """ No basetabs and no decorated tabs """
        class TestSpoke(Spoke):
            basetabs = ()

            auth = None  ## clear auth tab

            def test_tab(self):
                pass

        s = TestSpoke(mock.MagicMock(tab=False, action=False))

        assert s.tabs() == ()

    def test_tab_collection(self):
        """ A decorated method should be returned as tab """
        class TestSpoke(Spoke):
            @tab()
            def test_tab(self):
                pass

        s = TestSpoke(mock.MagicMock(tab=False, action=False))

        assert 'test_tab' in [x['id'] for x in s.tabs()]

    def test_tab_action_registry(self):
        """ tabs can be registered explicitly outside spokes """
        class TestSpoke(Spoke):
            pass

        s = TestSpoke(mock.MagicMock(tab=False, action=False))

        @tab()
        def tabhandler(handler, request, action):
            pass

        action_registry.register(tabhandler, 'tabhandler')

        assert 'tabhandler' in [x['id'] for x in s.tabs()]

    def test_tab_action_registry_restrct_spoke(self):
        """ tabs can be registered explicitly outside spokes,
            but if defined the spoke should match """
        class TestSpoke(Spoke):
            pass

        class Test2Spoke(Spoke):
            pass

        s1 = TestSpoke(mock.MagicMock(tab=False, action=False))
        s2 = Test2Spoke(mock.MagicMock(tab=False, action=False))

        @tab()
        def tabhandler(handler, request, action):
            pass

        action_registry.register(tabhandler, 'tabhandler', spoke=Test2Spoke)

        assert 'tabhandler' not in [x['id'] for x in s1.tabs()]
        assert 'tabhandler' in [x['id'] for x in s2.tabs()]
