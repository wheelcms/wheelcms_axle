from wheelcms_axle.node import Node, DuplicatePathException
from wheelcms_axle.node import InvalidPathException, CantRenameRoot, CantMoveToOffspring
from wheelcms_axle.node import NodeNotFound

import py.test

class TestNode(object):
    def test_root(self, client):
        """ verify we can get a (unique) root node """
        root1 = Node.root()
        root2 = Node.root()
        assert root1 == root2
        assert root1.isroot()

    def test_root_child(self, client):
        """ access a child on the root by its name """
        root = Node.root()
        child = root.add("child")
        assert root.child('child') == child

    def test_root_child_notfound(self, client):
        """ access a nonexisting child on the root by its name """
        root = Node.root()
        assert root.child('child') is None

    def test_nonroot_child(self, client):
        """ access a child outside the root by its name """
        root = Node.root()
        child = root.add("child")
        child2 = child.add("child")
        # import pytest; pytest.set_trace()
        assert child.child('child') == child2

    def test_nonroot_child_notfound(self, client):
        """ access a nonexisting child outside the root by its name """
        root = Node.root()
        child = root.add("child")
        assert child.child('child2') is None

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

    def test_addvalid(self, client):
        """ only letters, numbers, _- are allowed """
        root = Node.root()

        assert root.add("c")
        assert root.add("1")
        assert root.add("-")
        assert root.add("_")
        assert root.add("a1")
        assert root.add("aB1_-2")
        assert root.add("x" * Node.MAX_PATHLEN)

    def test_addinvalid(self, client):
        """ only letters, numbers, _- are allowed """
        root = Node.root()
        py.test.raises(InvalidPathException, root.add, "")
        py.test.raises(InvalidPathException, root.add, "c hild")
        py.test.raises(InvalidPathException, root.add, "child$")
        py.test.raises(InvalidPathException, root.add, "child/")
        py.test.raises(InvalidPathException, root.add, "child.")
        py.test.raises(InvalidPathException, root.add,
                       "x" * (Node.MAX_PATHLEN+1))

    def test_add_empty(self, client):
        """ a path or langslug map must be provided """
        root = Node.root()
        py.test.raises(InvalidPathException, root.add)

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

    def test_node_unattached(self, client):
        """ a node without content attached """
        root = Node.root()
        assert root.content() is None

    def test_root_lookup(self, client):
        """ get("") should implicitly create root node """
        assert Node.get("").isroot()

    def test_change_slug(self, client):
        """ change a slug """
        node = Node.root().add("aaa").add("bbb")
        assert node.slug() == "bbb"
        node.rename("ccc")
        node = Node.objects.get(pk=node.pk)
        assert node.slug() == "ccc"
        assert node.path == "/aaa/ccc"

    def test_change_slug_duplicate(self, client):
        """ change a slug """
        aaa = Node.root().add("aaa")
        aaa.add("bbb")
        node = aaa.add("bbb2")
        py.test.raises(DuplicatePathException, node.rename, "bbb")
        assert node.slug() == "bbb2"

    def test_rename_root(self, client):
        """ root cannot be renamed """
        py.test.raises(CantRenameRoot, lambda: Node.root().rename("x"))

    def test_rename_recursive(self, client):
        """ verify the rename is recursive """
        aaa = Node.root().add("aaa")
        bbb = aaa.add("bbb")
        bbb2 = aaa.add("bbb2")
        bbb_d = bbb.add("d")

        aaa.rename("ccc")
        assert Node.objects.get(pk=bbb.pk).path == "/ccc/bbb"
        assert Node.objects.get(pk=bbb2.pk).path == "/ccc/bbb2"
        assert Node.objects.get(pk=bbb_d.pk).path == "/ccc/bbb/d"

    def test_rename_recursive_similar(self, client):
        """ renaming /aaa should't affect /aaaa """
        aaa = Node.root().add("aaa")
        aaaa = Node.root().add("aaaa")
        aa = Node.root().add("aa")
        bbb = aaaa.add("bbb")
        bb = aa.add("bb")
        aaa.rename("ccc")
        assert Node.objects.get(pk=bbb.pk).path == "/aaaa/bbb"
        assert Node.objects.get(pk=bb.pk).path == "/aa/bb"

    def test_remove_single_root(self, client):
        """ single, non-recursive removal """
        root = Node.root()
        root.add("aaa")
        assert Node.get("/aaa")

        root.remove("aaa")
        assert not Node.get("/aaa")

    def test_remove_single_child(self, client):
        """ single, non-recursive removal """
        root = Node.root()
        child = root.add("aaa")
        child.add("bbb")

        assert Node.get("/aaa/bbb")

        child.remove("bbb")
        assert not Node.get("/aaa/bbb")

    def test_remove_notfound(self, client):
        """ verify exception when removing non-existing child """
        py.test.raises(NodeNotFound, Node.root().remove, "aaa")

    def test_remove_recursive(self, client):
        """ recursive removal """
        root = Node.root()
        child = root.add("aaa")
        child.add("b1")
        child.add("b2")
        assert Node.get("/aaa/b1")

        root.remove("aaa")
        assert not Node.get("/aaa/b1")
        assert not Node.get("/aaa/b2")

    def test_remove_recursive_child(self, client):
        """ recursive removal """
        root = Node.root()
        c1 = root.add("aaa")
        c2 = c1.add("bbb")
        c2.add("b1")
        c2.add("b2")
        assert Node.get("/aaa/bbb/b1")

        c1.remove("bbb")
        assert Node.get("/aaa")
        assert not Node.get("/aaa/bbb/b1")
        assert not Node.get("/aaa/bbb/b2")

    def test_remove_ignore_similar(self, client):
        """ removing /aaa shouldn't affect /aaaa """
        root = Node.root()
        root.add("aaa")
        root.add("aaaa")

        root.remove("aaa")
        assert Node.get("/aaaa")

    def test_reorder_position_before(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, after=c2)

        assert list(root.children()) == [c2, c1, c3]

    def test_reorder_position_after(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, before=c3)

        assert list(root.children()) == [c2, c1, c3]

    def test_reorder_position_end(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, after=c3)

        assert list(root.children()) == [c2, c3, c1]

    def test_reorder_position_start(self, client):
        """ childs are returned in order they were added """
        root = Node.root()
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c3, before=c1)

        assert list(root.children()) == [c3, c1, c2]

    def test_reorder_tight(self, client):
        """ heavy reordering without any spare space """
        root = Node.root()
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=1)
        c3 = root.add("c3", position=2)
        c4 = root.add("c4", position=3)

        root.move(c4, before=c1)
        root.move(c2, after=c3)
        root.move(c3, before=c2)

        assert list(root.children()) == [c4, c1, c3, c2]

    def test_reorder_oddcase1_after(self, client):
        """ move after a node where multiple follow """
        root = Node.root()
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, after=c2)

        assert list(root.children()) == [c2, c1, c3, c4]

    def test_reorder_oddcase1_before(self, client):
        """ move before a node where multiple follow
            Works because of latest()
        """
        root = Node.root()
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, before=c4)

        assert list(root.children()) == [c2, c3, c1, c4]

    def test_reorder_oddcase2(self, client):
        """ move after a node where none follow, Works because
            DoesNotExist is caught
        """
        root = Node.root()
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, after=c4)

        assert list(root.children()) == [c2, c3, c4, c1]

class TestNodeCopyPaste(object):
    ## cut/copy/paste
    def test_move_node(self, client):
        """ move a node and its descendants elsewhere """
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")

        res, success, failed = target.paste(src)

        assert Node.get('/target/src') == src
        assert Node.get('/target/src/child') == src_c
        assert Node.get('/src') is None
        assert res.path == "/target/src"


    def test_move_inside_offspring(self, client):
        """ A node cannot be moved to one of its offspring nodes. """
        root = Node.root()
        src = root.add("src")
        target = src.add("target")

        py.test.raises(CantMoveToOffspring, target.paste, src)

    def test_move_inside_self(self, client):
        """ A node cannot be moved to one of its offspring nodes. """
        root = Node.root()
        src = root.add("src")

        py.test.raises(CantMoveToOffspring, src.paste, src)

    def test_move_inside_offspring_root(self, client):
        """ A node cannot be moved to one of its offspring nodes.
            This, of course, also means root cannot be moved """
        root = Node.root()
        src = root.add("src")
        py.test.raises(CantMoveToOffspring, src.paste, root)

    def test_move_to_self(self, client):
        """ moving /foo to / """
        root = Node.root()
        src = root.add("src")
        res, success, failed = root.paste(src)

        assert res == src
        assert res.path == "/src"


    def test_move_node_inuse(self, client):
        """ pasting a node to a node containing a child with the same name,
            e.g. pasting /foo to /target when there's already a /target/foo
        """
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")
        target_src = target.add("src")

        # import pytest; pytest.set_trace()
        res, success, failed = target.paste(src)

        assert Node.get('/target/src') == target_src
        assert src.path != "/src"
        assert src.path != "/target/src"
        assert Node.get(src.path + "/child")

    def test_move_node_position(self, client):
        """ a node loses its original position when moved,
            it should always be moved to the bottom """
        root = Node.root()
        src = root.add("src", position=0)
        target = root.add("target")
        target_child = target.add("child", position=10)

        res, success, failed = target.paste(src)

        assert Node.get("/target/src").position > target_child.position

    ## test_copy_root
    ## test_copy_inside -> copy /foo to /foo (resulting in /foo/foo)

    ## how to handle content copy, and what if subtypes are not allowed?
    ## what if name conflict? E.g. /target/foo and then /foo -> /target?

    def test_copy_node(self, client):
        """ copy a node and its descendants elsewhere """
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")

        target.paste(src, copy=True)

        ## it has been copied and is not the original
        assert Node.get('/target/src') is not None
        assert Node.get('/target/src') != src
        assert Node.get('/target/src/child') is not None
        assert Node.get('/target/src/child') != src_c

        ## the original is still there
        assert Node.get('/src') is not None
        assert Node.get('/src') == src
        assert Node.get('/src/child') is not None
        assert Node.get('/src/child') == src_c

    def test_copy_node_position(self, client):
        """ a node loses its original position when copied,
            it should always be moved to the bottom """
        root = Node.root()
        src = root.add("src", position=0)
        target = root.add("target")
        target_child = target.add("child", position=10)

        res, success, failed = target.paste(src, copy=True)

        assert Node.get("/target/src").position > target_child.position

    def test_copy_node_inuse(self, client):
        """ pasting a node to a node containing a child with the same name,
            e.g. pasting /foo to /target when there's already a /target/foo
        """
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")
        target_src = target.add("src")

        res, success, failed = target.paste(src)

        assert res.path != "/target/src"
        assert Node.get(res.path + "/child")

    def test_copy_node_to_self(self, client):
        """ copy /foo to / """
        root = Node.root()
        src = root.add("src")
        res, success, failed = root.paste(src, copy=True)

        assert res.path != "/src"

    def test_copy_inside_offspring(self, client):
        """ A node can be copied to one of its offspring nodes """
        root = Node.root()
        src = root.add("src")
        target = src.add("target")

        res, success, failed = target.paste(src, copy=True)

        assert res.path == "/src/target/src"
        assert res != src

    def test_copy_root_inside_offspring(self, client):
        """ Copying root is a special case because it has an empty slug """
        root = Node.root()
        src = root.add("src")
        target = src.add("target")

        res, success, failed = target.paste(root, copy=True)

        assert res.path == "/src/target/root"
        assert res != src

    def test_move_node_duplicate_name(self, client):
        """ Move a node somewhere where there's already a similar slug """
        # issue #789
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        root_child = root.add("child")

        res, success, failed = root.paste(src_c)

        assert Node.get('/child') == root_child
        assert src_c.parent() == root
        assert src_c.path.startswith('/')

    def test_copy_node_duplicate_name(self, client):
        """ Move a node somewhere where there's already a similar slug """
        # issue #789
        root = Node.root()
        src = root.add("src")
        src_c = src.add("child")
        root_child = root.add("child")

        res, success, failed = root.paste(src_c, copy=True)

        assert Node.get('/child') == root_child
        assert res
        assert res.parent() == root
        assert res.path.startswith('/')

class TestNodeTranslation(object):
    """ test translation related stuff """
    def test_preferred_language_child(self, client):
        root = Node.root()
        sub = root.add("sub")
        sub_pref = root.child("sub", language="en")
        assert sub_pref.preferred_language == "en"
        sub_pref = root.child("sub", language="nl")
        assert sub_pref.preferred_language == "nl"

    def test_preferred_language_children(self, client):
        root = Node.root()
        sub = root.add("sub")

        root = Node.root(language="nl")
        child = root.children()[0]
        assert child.preferred_language == "nl"

    def test_preferred_language_content(self, client):
        root = Node.root()
        sub = root.add("sub")
        from .models import Type1

        en = Type1(title="EN", node=sub, language="en").save()
        nl = Type1(title="NL", node=sub, language="nl").save()

        assert root.child("sub", language="nl").content() == nl
        assert root.child("sub", language="en").content() == en

    def test_node_equality(self, client):
        root = Node.root()
        sub = root.add("sub")
        sub_nl = Node.root(language="nl").children()[0]
        sub_en = Node.root(language="en").children()[0]

        assert sub_nl != sub_en
        assert sub_nl != sub

        sub.preferred_language = "nl"
        assert sub == sub_nl

