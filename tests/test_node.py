from wheelcms_axle.models import Node, DuplicatePathException
from wheelcms_axle.models import InvalidPathException, NodeInUse
import py.test

class TestNode(object):
    def test_root(self, client):
        """ verify we can get a (unique) root node """
        root1 = Node.root()
        root2 = Node.root()
        assert root1 == root2
        assert root1.isroot()

    def test_add_child_root(self, client):
        """ adding a child to the root results in a new node """
        root = Node.root()
        child = root.add("child")
        assert isinstance(child, Node)
        assert child.path == "/child"
        assert root.children().count() == 1
        assert root.children()[0] == child
        assert child.parent() == root

    def test_add_child_sub(self, client):
        """ adding a child to a nonroot """
        root = Node.root()
        top = root.add("top")
        sub = top.add("sub")

        assert root.children().count() == 1
        assert top.children().count() == 1

        assert isinstance(sub, Node)
        assert sub.path == "/top/sub"
        assert sub.children().count() == 0
        assert top.children()[0] == sub
        assert sub.parent() == top

    def test_unique(self, client):
        """ paths are unique, you cannot add  the same name twice """
        root = Node.root()
        root.add("child")

        py.test.raises(DuplicatePathException, root.add, "child")
        py.test.raises(DuplicatePathException, root.add, "CHILD")
        py.test.raises(DuplicatePathException, root.add, "Child")

    def test_invalid(self, client):
        """ only letters, numbers, _- are allowed """
        root = Node.root()

        assert root.add("c")
        assert root.add("1")
        assert root.add("-")
        assert root.add("_")
        assert root.add("a1")
        assert root.add("aB1_-2")
        assert root.add("x" * Node.MAX_PATHLEN)

        py.test.raises(InvalidPathException, root.add, "")
        py.test.raises(InvalidPathException, root.add, "c hild")
        py.test.raises(InvalidPathException, root.add, "child$")
        py.test.raises(InvalidPathException, root.add, "child/")
        py.test.raises(InvalidPathException, root.add, "child.")
        py.test.raises(InvalidPathException, root.add,
                       "x" * (Node.MAX_PATHLEN+1))

    def test_implicit_position(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        assert list(root.children()) == [c1, c2, c3]

    def test_explicit_position(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1", position=20)
        c2 = root.add("c2", position=10)
        c3 = root.add("c3", position=30)

        assert list(root.children()) == [c2, c1, c3]

    def test_position_after_simple(self, client):
        """ insert a node directly after another """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3", after=c1)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_after_conflict(self, client):
        """ insert a node directly after another, with position conflict  """
        root = Node.root()
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", after=c1)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_after_end(self, client):
        """ insert a node at the end """
        root = Node.root()
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", after=c2)

        children = list(root.children())
        assert children == [c1, c2, c3]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_simple(self, client):
        """ insert a node directly before another """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3", before=c2)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_conflict(self, client):
        """ insert a node directly before another, with position conflict  """
        root = Node.root()
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", before=c2)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_begin(self, client):
        """ insert a node directly before the first item """
        root = Node.root()
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", before=c1)

        children = list(root.children())
        assert children == [c3, c1, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_twice(self, client):
        """ inserting at the same position twice - it's allowed
            but results in undetermined order """
        root = Node.root()
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=100)

        children = root.children()
        assert set(children) == set((c3, c1, c2))
        assert children[0].position == children[1].position \
               == children[2].position

    def test_direct_root(self, client):
        """ retrieve the root node directly through its path """
        n = Node.root()
        assert Node.get("") == n

    def test_direct_path(self, client):
        """ retrieve a node directly through its path """
        n = Node.root().add("a").add("b").add("c")
        assert Node.get("/a/b/c") == n

    def test_direct_path_notfound(self, client):
        """ retrieve a node directly through its path """
        Node.root().add("a").add("b").add("c")
        assert Node.get("/d/e/f") is None

    def test_move_after(self, client):
        """ move an existing node after another node.
            Not yet implemented; implementation requires 
            refactoring of add() code (which should do create
            at bottom + move) """
        py.test.skip("To do")

    def test_change_slug(self, client):
        """ change a slug """
        node = Node.root().add("aaa").add("bbb")
        assert node.slug() == "bbb"
        node.set_slug("ccc")
        assert node.slug() == "ccc"

    def test_change_slug_duplicate(self, client):
        """ change a slug """
        aaa = Node.root().add("aaa")
        aaa.add("bbb")
        node = aaa.add("bbb2")
        py.test.raises(DuplicatePathException, node.set_slug, "bbb")
        assert node.slug() == "bbb2"

    def test_node_unattached(self, client):
        """ a node without content attached """
        root = Node.root()
        assert root.content() is None

class TestNodeBase(object):
    """ The base class of a node can be altered. """

