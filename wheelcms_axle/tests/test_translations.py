from wheelcms_axle.node import Node, DuplicatePathException
from django.utils import translation
from django.conf import settings
import pytest


class TestRootNode(object):
    def setup(self):
        settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))
        settings.FALLBACK = False

    def test_disabled(self, client):
        """ multi language support disabled """
        pytest.skip("todo")

    def test_setup(self, client):
        translation.activate('en')
        root = Node.root()
        assert root.path == ''
        assert root.slug() == ''
        assert root.get_path('en') == ''
        assert root.get_path('nl') == ''
        assert root.get_path('fr') == ''

        assert root.slug('en') == ''
        assert root.slug('nl') == ''
        assert root.slug('fr') == ''

        assert root.isroot()

    def test_non_supported_language_root(self, client):
        """ root is always present, even for unsupported language """
        translation.activate('de')
        root = Node.get("")
        assert root is not None

    def test_non_supported_language(self, client):
        """ a non-supported language, no fallback """
        translation.activate('de')
        root = Node.root()
        child = root.add("child")
        assert Node.get("/child", language="de") is None

    def test_default(self, client):
        settings.FALLBACK = 'en'
        root = Node.root()
        assert root.path == ''

    ## root cannot be renamed

class TestNode(object):
    def setup(self):
        from django.conf import settings
        settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))

    def test_node(self, client):
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        en_child = Node.get("/child")
        assert en_child == child
        assert en_child.path == "/child"
        assert en_child.slug() == "child"
        assert en_child.get_path("en") == "/child"
        assert en_child.slug("en") == "child"
        assert en_child.get_path("nl") == "/child"
        assert en_child.slug("nl") == "child"
        assert en_child.get_path("fr") == "/child"
        assert en_child.slug("fr") == "child"

    def test_node_slug_language(self, client):
        """ A node with different slugs for different languages """
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        child.rename("kind", language="nl")
        child.rename("enfant", language="fr")

        translation.activate('nl')
        nl_child = Node.get("/kind")
        assert nl_child == child
        assert nl_child.path == "/kind"
        assert nl_child.slug() == "kind"
        assert nl_child.get_path("nl") == "/kind"

        assert nl_child.get_path("en") == "/child"
        assert nl_child.slug("en") == "child"
        assert nl_child.get_path("fr") == "/enfant"
        assert nl_child.slug("fr") == "enfant"

    def test_node_slug_offspring_language(self, client):
        """ A node with different slugs for different languages,
            with children"""
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        child1 = child.add("grandchild1")
        child2 = child.add("grandchild2")

        # import pytest; pytest.set_trace()
        child.rename("kind", language="nl")
        child2.rename("kleinkind2", language="nl")


        translation.activate('nl')
        nl_child2 = Node.get("/kind/kleinkind2")
        assert nl_child2 == child2
        assert nl_child2.path == "/kind/kleinkind2"

        nl_child1 = Node.get("/kind/grandchild1")
        assert nl_child1 == child1
        assert nl_child1.path == "/kind/grandchild1"

    def test_add_different_slugs(self, client):
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        child.rename("kind", language="nl")
        grandchild = child.add("grandchild")

        assert grandchild.get_path(language="nl") == "/kind/grandchild"
        assert grandchild.get_path(language="en") == "/child/grandchild"
        assert Node.get("/child/grandchild", language="nl") is None
        assert Node.get("/kind/grandchild", language="en") is None

    def test_rename_default(self, client):
        """ rename on a node with no explicit language specified,
            which should rename all nodes, if possible """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")

        r1.rename("rr1")

        assert r1.paths.count() == 4  ## "any" gets added implicitly
        assert r1.path == "/rr1"
        translation.activate('nl')
        assert r1.path == "/rr1"
        translation.activate('fr')
        assert r1.path == "/rr1"
        translation.activate('any')
        assert r1.path == "/rr1"

    def test_rename_default_recursive(self, client):
        """ rename on a node with no explicit language specified,
            which should rename all nodes, if possible """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r2 = r1.add("sub")

        r1.rename("rr1")

        assert r2.paths.count() == 4  ## "any" gets added implicitly
        assert r2.path == "/rr1/sub"
        translation.activate('nl')
        assert r2.path == "/rr1/sub"
        translation.activate('fr')
        assert r2.path == "/rr1/sub"
        translation.activate('any')
        assert r2.path == "/rr1/sub"

    def test_rename_duplicate(self, client):
        """ a trivial duplicate slug failure """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r2 = root.add("r2")

        pytest.raises(DuplicatePathException,
                      r1.rename, "r2", language="fr")


    def test_rename_complex(self, client):
        """ a rather confusing case:
            try to swap /r1 and /r2 for a specific language """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r11 = r1.add("r11")
        r2 = root.add("r2")
        r22 = r2.add("r22")

        r1.rename("rX", language="nl")
        r2.rename("r1", language="nl")
        r1.rename("r2", language="nl")

        assert Node.get("/r1", language="nl") == r2
        assert Node.get("/r2", language="nl") == r1

    def test_rename_complex_duplicate(self, client):
        """ a conflict within a specific language """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r11 = r1.add("r11")
        r2 = root.add("r2")
        r22 = r2.add("r11")

        pytest.raises(DuplicatePathException, r1.rename, "r2", language="nl")

    def test_node_child(self, client):
        """ test the node.child method """
        translation.activate('en')
        root = Node.root()
        child = root.add("child")

        assert root.child("child") == child

    def test_node_child_notfound(self, client):
        translation.activate('en')
        root = Node.root()
        assert root.child("x") is None

    def test_node_child_langswitch(self, client):
        """ test the node.child method """
        translation.activate('en')
        root = Node.root()
        child = root.add("child")

        translation.activate('fr')
        assert root.child("child") == child

    def test_children(self, client):
        """ find the children of a node """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r2 = root.add("r2")
        r3 = root.add("r3")

        r2.rename("rr2", language="en")

        assert list(root.children()) == [r1, r2, r3]
        assert root.child("rr2", "en") == r2
        assert root.child("r2", "fr") == r2

        assert root.get("/rr2", "en") == r2
        assert root.get("/r2", "fr") == r2


    def test_offspring(self, client):
        pytest.skip("todo")

    def test_remove(self, client):
        """ remove a node by one of it's path's """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        translation.activate('fr')
        root.remove("r1")
        assert root.child("r1") is None

    def test_remove_recursive(self, client):
        """ remove a node by one of it's path's """
        translation.activate('en')
        root = Node.root()
        r1 = root.add("r1")
        r2 = r1.add("r2")

        translation.activate('fr')
        root.remove("r1")
        assert root.get("/r1/r2") is None

    def test_create_map(self, client):
        root = Node.root()
        r = root.add(langslugs=dict(fr="fr", en="en", nl="nl"))

        assert Node.get("/fr", language="fr") == \
               Node.get("/en", language="en") == \
               Node.get("/nl", language="nl") == r

    def test_move(self, client):
        ## meteen recursief
        root = Node.root()
        src = root.add(langslugs=dict(fr="source", nl="bron", en="src"))
        src2 = src.add(langslugs=dict(fr="fr", nl="nl", en="en"))

        # import pytest;pytest.set_trace()
        target = root.add(langslugs=dict(fr="destination",
                                         nl="doel", en="target"))

        target.paste(src, copy=False)

        assert Node.get("/source", language="fr") is None
        assert Node.get("/destination/source", language="fr") == src
        assert Node.get("/destination/source/fr", language="fr") == src2
        assert Node.get("/doel/bron", language="nl") == src
        assert Node.get("/doel/bron/nl", language="nl") == src2
        assert Node.get("/target/src", language="en") == src
        assert Node.get("/target/src/en", language="en") == src2

    def test_copy(self, client):
        root = Node.root()
        src = root.add(langslugs=dict(fr="source", nl="bron", en="src"))
        src2 = src.add(langslugs=dict(fr="fr", nl="nl", en="en"))
        target = root.add(langslugs=dict(fr="destination",
                                         nl="doel", en="target"))

        target.paste(src, copy=True)

        assert Node.get("/source", language="fr") == src
        assert Node.get("/destination/source", language="fr") is not None
        assert Node.get("/destination/source/fr", language="fr") is not None
        assert Node.get("/destination/source", language="fr") != src
        assert Node.get("/doel/bron", language="nl") is not None
        assert Node.get("/doel/bron/nl", language="nl") is not None
        assert Node.get("/doel/bron", language="nl") != src
        assert Node.get("/target/src", language="en") is not None
        assert Node.get("/target/src/en", language="en") is not None
        assert Node.get("/target/src", language="en") != src

class TestContent(object):
    pass

##
## Basis testcase:
## 1 node met 3x content per taal, allemaal zelfde slug
## 2 nodes met 6x content, verschillende slugs

## Test slug rename through handler / form
## zie o.a. test_content_crud (test_tags)
## en test_spokes test_slug_generate_reserved_existing

