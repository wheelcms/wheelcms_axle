import mock
from drole.types import Permission
from wheelcms_axle.spoke import Spoke, tab

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

        s = TestSpoke(mock.MagicMock(tab=False, action=False))

        assert s.tabs() == ()

    def test_basetab_action(self):
        """ No basetabs and no decorated tabs """
        class TestSpoke(Spoke):
            basetabs = ()

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
