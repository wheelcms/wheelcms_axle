import mock
import pytest

from wheelcms_axle.templatetags.topnav import navigation_items
from wheelcms_axle.tests.models import Type1Type

from .test_auth import anon_request

@pytest.mark.usefixtures("localtyperegistry")
class TestNavigation(object):
    type = Type1Type
    """
        Test the topnav navigation generation. More
        specifically, visible / accessible content
        that's "navigatable"
    """
    def test_unattached_empty_root(self, client, root, anon_request):
        """ no content on root, no children """
        res = navigation_items(anon_request, root)

        assert 'toplevel' in res
        assert res['toplevel'] == []

    def test_attached_empty_root(self, client, root, anon_request):
        """ content on root, no children """
        Type1Type.create(node=root).save()
        res = navigation_items(anon_request, root)

        assert 'toplevel' in res
        assert res['toplevel'] == []

    def test_single_child_visible(self, client, root, anon_request):
        """ single accessible child """
        c = Type1Type.create(navigation=True, node=root.add("c1")).save()
        with mock.patch("wheelcms_axle.auth.has_access", return_value=True):
            res = navigation_items(anon_request, root)

            assert len(res['toplevel']) == 1
            assert res['toplevel'][0]['url'] == c.instance.get_absolute_url()

    def test_single_child_notvisible(self, client, root, anon_request):
        """ single inaccessible child """
        Type1Type.create(navigation=True, node=root.add("c1")).save()
        with mock.patch("wheelcms_axle.auth.has_access", return_value=False):
            res = navigation_items(anon_request, root)

            assert len(res['toplevel']) == 0

    def test_second_level_visible(self, client, root, anon_request):
        """ child with subcontent, accessible """
        n1 = root.add("c1")
        n1_child = n1.add("c2")
        Type1Type.create(navigation=True, node=n1).save()
        c2 = Type1Type.create(navigation=True, node=n1_child).save()

        with mock.patch("wheelcms_axle.auth.has_access", return_value=True):
            res = navigation_items(anon_request, root)

            assert len(res['toplevel']) == 1
            assert len(res['toplevel'][0]['sub']) == 1
            assert res['toplevel'][0]['sub'][0]['url'] == \
                   c2.instance.get_absolute_url()

    def test_second_level_invisible(self, client, root, anon_request):
        """ toplevel accessible, sublevel not """
        n1 = root.add("c1")
        n1_child = n1.add("c2")
        Type1Type.create(navigation=True, node=n1).save()
        c2 = Type1Type.create(navigation=True, node=n1_child).save()

        def mocked_has_access(request, type, spoke, perm):
            if spoke == c2:
                return False
            return True

        with mock.patch("wheelcms_axle.auth.has_access", mocked_has_access):
            res = navigation_items(anon_request, root)

            assert len(res['toplevel']) == 1
            assert len(res['toplevel'][0]['sub']) == 0

    def test_active(self, client, root, anon_request):
        """ Correct item should be 'active' if accessed through a
            childnode of it """
        n1 = root.add("c1")
        n2 = root.add("c2")
        n1_child = n1.add("c1_c")
        n2_child = n2.add("c2_c")

        Type1Type.create(navigation=True, node=n1).save()
        Type1Type.create(navigation=True, node=n1_child).save()
        Type1Type.create(navigation=True, node=n2).save()
        Type1Type.create(navigation=True, node=n2_child).save()

        with mock.patch("wheelcms_axle.auth.has_access", return_value=True):
            res = navigation_items(anon_request, n2_child)

            assert len(res['toplevel']) == 2
            assert not res['toplevel'][0]['active']
            assert res['toplevel'][1]['active']
