from wheelcms_axle.node import Node, DuplicatePathException
from wheelcms_axle.node import InvalidPathException, CantRenameRoot
from wheelcms_axle.node import CantMoveToOffspring
from wheelcms_axle.node import NodeNotFound
from .test_urls import Base

import pytest

class TestNode(object):
    def test_root(self, client):
        """ verify we can get a (unique) root node """
        root1 = Node.root()
        root2 = Node.root()
        assert root1 == root2
        assert root1.isroot()

    def test_root_child(self, client, root):
        """ access a child on the root by its name """
        child = root.add("child")
        assert root.child('child') == child

    def test_root_child_notfound(self, client, root):
        """ access a nonexisting child on the root by its name """
        assert root.child('child') is None

    def test_nonroot_child(self, client, root):
        """ access a child outside the root by its name """
        child = root.add("child")
        child2 = child.add("child")
        # import pytest; pytest.set_trace()
        assert child.child('child') == child2

    def test_nonroot_child_notfound(self, client, root):
        """ access a nonexisting child outside the root by its name """
        child = root.add("child")
        assert child.child('child2') is None

    def test_add_child_root(self, client, root):
        """ adding a child to the root results in a new node """
        child = root.add("child")
        assert isinstance(child, Node)
        assert child.path == "/child"
        assert root.children().count() == 1
        assert root.children()[0] == child
        assert child.parent() == root

    def test_add_child_sub(self, client, root):
        """ adding a child to a nonroot """
        top = root.add("top")
        sub = top.add("sub")

        assert root.children().count() == 1
        assert top.children().count() == 1

        assert isinstance(sub, Node)
        assert sub.path == "/top/sub"
        assert sub.children().count() == 0
        assert top.children()[0] == sub
        assert sub.parent() == top

    def test_unique(self, client, root):
        """ paths are unique, you cannot add  the same name twice """
        root.add("child")

        pytest.raises(DuplicatePathException, root.add, "child")
        pytest.raises(DuplicatePathException, root.add, "CHILD")
        pytest.raises(DuplicatePathException, root.add, "Child")

    def test_addvalid(self, client, root):
        """ only letters, numbers, _- are allowed """
        assert root.add("c")
        assert root.add("1")
        assert root.add("-")
        assert root.add("_")
        assert root.add("a1")
        assert root.add("aB1_-2")
        assert root.add("x" * Node.MAX_PATHLEN)

    def test_addinvalid(self, client, root):
        """ only letters, numbers, _- are allowed """
        pytest.raises(InvalidPathException, root.add, "")
        pytest.raises(InvalidPathException, root.add, "c hild")
        pytest.raises(InvalidPathException, root.add, "child$")
        pytest.raises(InvalidPathException, root.add, "child/")
        pytest.raises(InvalidPathException, root.add, "child.")
        pytest.raises(InvalidPathException, root.add,
                       "x" * (Node.MAX_PATHLEN+1))

    def test_add_empty(self, client, root):
        """ a path or langslug map must be provided """
        pytest.raises(InvalidPathException, root.add)

    def test_implicit_position(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        assert list(root.children()) == [c1, c2, c3]

    def test_explicit_position(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1", position=20)
        c2 = root.add("c2", position=10)
        c3 = root.add("c3", position=30)

        assert list(root.children()) == [c2, c1, c3]

    def test_position_after_simple(self, client, root):
        """ insert a node directly after another """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3", after=c1)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_after_conflict(self, client, root):
        """ insert a node directly after another, with position conflict  """
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", after=c1)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_after_end(self, client, root):
        """ insert a node at the end """
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", after=c2)

        children = list(root.children())
        assert children == [c1, c2, c3]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_simple(self, client, root):
        """ insert a node directly before another """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3", before=c2)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_conflict(self, client, root):
        """ insert a node directly before another, with position conflict  """
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", before=c2)

        children = list(root.children())
        assert children == [c1, c3, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_before_begin(self, client, root):
        """ insert a node directly before the first item """
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=101)
        c3 = root.add("c3", before=c1)

        children = list(root.children())
        assert children == [c3, c1, c2]
        assert children[0].position < children[1].position \
               < children[2].position

    def test_position_twice(self, client, root):
        """ inserting at the same position twice - it's allowed
            but results in undetermined order """
        c1 = root.add("c1", position=100)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=100)

        children = root.children()
        assert set(children) == set((c3, c1, c2))
        assert children[0].position == children[1].position \
               == children[2].position

    def test_direct_root(self, client, root):
        """ retrieve the root node directly through its path """
        assert Node.get("") == root

    def test_direct_path(self, client, root):
        """ retrieve a node directly through its path """
        n = root.add("a").add("b").add("c")
        assert Node.get("/a/b/c") == n

    def test_direct_path_notfound(self, client, root):
        """ retrieve a node directly through its path """
        root.add("a").add("b").add("c")
        assert Node.get("/d/e/f") is None

    def test_move_after(self, client):
        """ move an existing node after another node.
            Not yet implemented; implementation requires 
            refactoring of add() code (which should do create
            at bottom + move) """
        pytest.skip("To do")

    def test_node_unattached(self, client, root):
        """ a node without content attached """
        assert root.content() is None

    def test_root_lookup(self, client):
        """ get("") should implicitly create root node """
        assert Node.get("").isroot()

    def test_change_slug(self, client, root):
        """ change a slug """
        node = root.add("aaa").add("bbb")
        assert node.slug() == "bbb"
        node.rename("ccc")
        node = Node.objects.get(pk=node.pk)
        assert node.slug() == "ccc"
        assert node.path == "/aaa/ccc"

    def test_change_slug_duplicate(self, client, root):
        """ change a slug """
        aaa = root.add("aaa")
        aaa.add("bbb")
        node = aaa.add("bbb2")
        pytest.raises(DuplicatePathException, node.rename, "bbb")
        assert node.slug() == "bbb2"

    def test_rename_root(self, client, root):
        """ root cannot be renamed """
        pytest.raises(CantRenameRoot, lambda: root.rename("x"))

    def test_rename_recursive(self, client, root):
        """ verify the rename is recursive """
        aaa = root.add("aaa")
        bbb = aaa.add("bbb")
        bbb2 = aaa.add("bbb2")
        bbb_d = bbb.add("d")

        aaa.rename("ccc")
        assert Node.objects.get(pk=bbb.pk).path == "/ccc/bbb"
        assert Node.objects.get(pk=bbb2.pk).path == "/ccc/bbb2"
        assert Node.objects.get(pk=bbb_d.pk).path == "/ccc/bbb/d"

    def test_rename_recursive_similar(self, client, root):
        """ renaming /aaa should't affect /aaaa """
        aaa = root.add("aaa")
        aaaa = root.add("aaaa")
        aa = root.add("aa")
        bbb = aaaa.add("bbb")
        bb = aa.add("bb")
        aaa.rename("ccc")
        assert Node.objects.get(pk=bbb.pk).path == "/aaaa/bbb"
        assert Node.objects.get(pk=bb.pk).path == "/aa/bb"

    def test_remove_single_root(self, client, root):
        """ single, non-recursive removal """
        root.add("aaa")
        assert Node.get("/aaa")

        root.remove("aaa")
        assert not Node.get("/aaa")

    def test_remove_single_child(self, client, root):
        """ single, non-recursive removal """
        child = root.add("aaa")
        child.add("bbb")

        assert Node.get("/aaa/bbb")

        child.remove("bbb")
        assert not Node.get("/aaa/bbb")

    def test_remove_notfound(self, client, root):
        """ verify exception when removing non-existing child """
        pytest.raises(NodeNotFound, root.remove, "aaa")

    def test_remove_recursive(self, client, root):
        """ recursive removal """
        child = root.add("aaa")
        child.add("b1")
        child.add("b2")
        assert Node.get("/aaa/b1")

        root.remove("aaa")
        assert not Node.get("/aaa/b1")
        assert not Node.get("/aaa/b2")

    def test_remove_recursive_child(self, client, root):
        """ recursive removal """
        c1 = root.add("aaa")
        c2 = c1.add("bbb")
        c2.add("b1")
        c2.add("b2")
        assert Node.get("/aaa/bbb/b1")

        c1.remove("bbb")
        assert Node.get("/aaa")
        assert not Node.get("/aaa/bbb/b1")
        assert not Node.get("/aaa/bbb/b2")

    def test_remove_ignore_similar(self, client, root):
        """ removing /aaa shouldn't affect /aaaa """
        root.add("aaa")
        root.add("aaaa")

        root.remove("aaa")
        assert Node.get("/aaaa")

    def test_reorder_position_before(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, after=c2)

        assert list(root.children()) == [c2, c1, c3]

    def test_reorder_position_after(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, before=c3)

        assert list(root.children()) == [c2, c1, c3]

    def test_reorder_position_end(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c1, after=c3)

        assert list(root.children()) == [c2, c3, c1]

    def test_reorder_position_start(self, client, root):
        """ childs are returned in order they were added """
        c1 = root.add("c1")
        c2 = root.add("c2")
        c3 = root.add("c3")

        root.move(c3, before=c1)

        assert list(root.children()) == [c3, c1, c2]

    def test_reorder_tight(self, client, root):
        """ heavy reordering without any spare space """
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=1)
        c3 = root.add("c3", position=2)
        c4 = root.add("c4", position=3)

        root.move(c4, before=c1)
        root.move(c2, after=c3)
        root.move(c3, before=c2)

        assert list(root.children()) == [c4, c1, c3, c2]

    def test_reorder_oddcase1_after(self, client, root):
        """ move after a node where multiple follow """
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, after=c2)

        assert list(root.children()) == [c2, c1, c3, c4]

    def test_reorder_oddcase1_before(self, client, root):
        """ move before a node where multiple follow
            Works because of latest()
        """
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, before=c4)

        assert list(root.children()) == [c2, c3, c1, c4]

    def test_reorder_oddcase2(self, client, root):
        """ move after a node where none follow, Works because
            DoesNotExist is caught
        """
        c1 = root.add("c1", position=0)
        c2 = root.add("c2", position=100)
        c3 = root.add("c3", position=200)
        c4 = root.add("c4", position=300)

        root.move(c1, after=c4)

        assert list(root.children()) == [c2, c3, c4, c1]

class TestNodeCopyPaste(Base):
    urls = 'wheelcms_axle.tests.urls_root'
    ## cut/copy/paste
    def test_move_node(self, client, root):
        """ move a node and its descendants elsewhere """
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")

        res, success, failed = target.paste(src)

        assert Node.get('/target/src') == src
        assert Node.get('/target/src/child') == src_c
        assert Node.get('/src') is None
        assert res.path == "/target/src"


    def test_move_inside_offspring(self, client, root):
        """ A node cannot be moved to one of its offspring nodes. """
        src = root.add("src")
        target = src.add("target")

        pytest.raises(CantMoveToOffspring, target.paste, src)

    def test_move_inside_self(self, client, root):
        """ A node cannot be moved to one of its offspring nodes. """
        src = root.add("src")

        pytest.raises(CantMoveToOffspring, src.paste, src)

    def test_move_inside_offspring_root(self, client, root):
        """ A node cannot be moved to one of its offspring nodes.
            This, of course, also means root cannot be moved """
        src = root.add("src")
        pytest.raises(CantMoveToOffspring, src.paste, root)

    def test_move_to_self(self, client, root):
        """ moving /foo to / """
        src = root.add("src")
        res, success, failed = root.paste(src)

        assert res == src
        assert res.path == "/src"


    def test_move_node_inuse(self, client, root):
        """ pasting a node to a node containing a child with the same name,
            e.g. pasting /foo to /target when there's already a /target/foo
        """
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

    def test_move_node_position(self, client, root):
        """ a node loses its original position when moved,
            it should always be moved to the bottom """
        src = root.add("src", position=0)
        target = root.add("target")
        target_child = target.add("child", position=10)

        res, success, failed = target.paste(src)

        assert Node.get("/target/src").position > target_child.position

    ## test_copy_root
    ## test_copy_inside -> copy /foo to /foo (resulting in /foo/foo)

    ## how to handle content copy, and what if subtypes are not allowed?
    ## what if name conflict? E.g. /target/foo and then /foo -> /target?

    def test_copy_node(self, client, root):
        """ copy a node and its descendants elsewhere """
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

    def test_copy_node_position(self, client, root):
        """ a node loses its original position when copied,
            it should always be moved to the bottom """
        src = root.add("src", position=0)
        target = root.add("target")
        target_child = target.add("child", position=10)

        res, success, failed = target.paste(src, copy=True)

        assert Node.get("/target/src").position > target_child.position

    def test_copy_node_inuse(self, client, root):
        """ pasting a node to a node containing a child with the same name,
            e.g. pasting /foo to /target when there's already a /target/foo
        """
        src = root.add("src")
        src_c = src.add("child")
        target = root.add("target")
        target_src = target.add("src")

        res, success, failed = target.paste(src)

        assert res.path != "/target/src"
        assert Node.get(res.path + "/child")

    def test_copy_node_to_self(self, client, root):
        """ copy /foo to / """
        src = root.add("src")
        res, success, failed = root.paste(src, copy=True)

        assert res.path != "/src"

    def test_copy_inside_offspring(self, client, root):
        """ A node can be copied to one of its offspring nodes """
        src = root.add("src")
        target = src.add("target")

        res, success, failed = target.paste(src, copy=True)

        assert res.path == "/src/target/src"
        assert res != src

    def test_copy_root_inside_offspring(self, client, root):
        """ Copying root is a special case because it has an empty slug """
        src = root.add("src")
        target = src.add("target")

        res, success, failed = target.paste(root, copy=True)

        assert res.path == "/src/target/root"
        assert res != src

    def test_move_node_duplicate_name(self, client, root):
        """ Move a node somewhere where there's already a similar slug """
        # issue #789
        src = root.add("src")
        src_c = src.add("child")
        root_child = root.add("child")

        res, success, failed = root.paste(src_c)

        assert Node.get('/child') == root_child
        assert src_c.parent() == root
        assert src_c.path.startswith('/')

    def test_copy_node_duplicate_name(self, client, root):
        """ Move a node somewhere where there's already a similar slug """
        # issue #789
        src = root.add("src")
        src_c = src.add("child")
        root_child = root.add("child")

        res, success, failed = root.paste(src_c, copy=True)

        assert Node.get('/child') == root_child
        assert res
        assert res.parent() == root
        assert res.path.startswith('/')

    def test_get_absolute_url(self, client, root):
        """ related to issue #799 - get_absolute_url on unattached node """
        child = root.add('foo')
        assert child.get_absolute_url() == '/foo/'

from .models import Type1, Type1Type

@pytest.mark.usefixtures("localtyperegistry")
class TestNodeTranslation(Base):
    """ test translation related stuff """
    type = Type1Type

    urls = 'wheelcms_axle.tests.urls_root'

    def test_preferred_language_child(self, client, root):
        sub = root.add("sub")
        sub_pref = root.child("sub", language="en")
        assert sub_pref.preferred_language == "en"
        sub_pref = root.child("sub", language="nl")
        assert sub_pref.preferred_language == "nl"

    def test_preferred_language_children(self, client, root):
        sub = root.add("sub")

        root = Node.root(language="nl")
        child = root.children()[0]
        assert child.preferred_language == "nl"

    def test_preferred_language_content(self, client, root):
        sub = root.add("sub")

        en = Type1(title="EN", node=sub, language="en").save()
        nl = Type1(title="NL", node=sub, language="nl").save()

        assert root.child("sub", language="nl").content() == nl
        assert root.child("sub", language="en").content() == en

    def test_node_equality(self, client, root):
        sub = root.add("sub")
        sub_nl = Node.root(language="nl").children()[0]
        sub_en = Node.root(language="en").children()[0]

        assert sub_nl != sub_en
        assert sub_nl != sub

        sub.preferred_language = "nl"
        assert sub == sub_nl

    def test_get_absolute_url(self, client, root):
        """ related to issue #799 - get_absolute_url on unattached node,
            multilingual """
        child = root.add(langslugs=dict(en="fooen", nl="foonl"))

        assert child.get_absolute_url(language='en') == '/fooen/'
        assert child.get_absolute_url(language='nl') == '/foonl/'
