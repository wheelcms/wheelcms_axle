from wheelcms_axle.models import Node
from wheelcms_axle.queries import get_visible_children
from wheelcms_axle.tests.models import Type1, Type2

class TestVisibleChildrenQueries(object):
    """
        Test queries related to visible children
    """
    def test_empty(self, client):
        """ a node without any children """
        root = Node.root()
        testable = root.add("sub")
        assert get_visible_children(testable).count() == 0

    def test_not_published(self, client):
        """ content that's in navigation but not published """
        root = Node.root()
        testable = root.add("sub")
        child = testable.add("child")
        content = Type1(node=child, navigation=True)
        content.save()

        assert get_visible_children(testable).count() == 0

    def test_not_visible(self, client):
        """ content that's published but not in navigation """
        root = Node.root()
        testable = root.add("sub")
        child = testable.add("child")
        content = Type1(node=child, state="published")
        content.save()

        assert get_visible_children(testable).count() == 0

    def test_published(self, client):
        """ content that's in navigation but not published """
        root = Node.root()
        testable = root.add("sub")
        child = testable.add("child")
        content = Type1(node=child, navigation=True, state="published")
        content.save()

        assert get_visible_children(testable).count() == 1
        assert get_visible_children(testable).get() == content.node

    def test_mix(self, client):
        """ a mix of types and states """
        root = Node.root()
        testable = root.add("sub")
        ch1 = Type1(node=testable.add("ch1"), navigation=True,
                    state="published").save()
        ch2 = Type1(node=testable.add("ch2"), navigation=False,
                    state="published").save()
        ch3 = Type2(node=testable.add("ch3"), navigation=True,
                    state="published").save()
        ch4 = Type1(node=testable.add("ch4"), navigation=True,
                    state="private").save()
        ch5 = Type1(node=testable.add("ch5"), navigation=True,
                    state="published").save()

        visible = list(get_visible_children(testable))
        assert visible == [ch1.node, ch3.node, ch5.node]
