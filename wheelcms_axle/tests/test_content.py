import pytest

from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User

from wheelcms_axle.node import Node, NodeInUse
from wheelcms_axle.content import Content, ContentCopyFailed
from wheelcms_axle.content import ContentCopyNotSupported
from wheelcms_axle.tests.models import Type1, Type2, TypeM2M, TypeUnique

from django.conf import settings

class TestContent(object):
    """ Test content / content-node related stuff """
    def setup(self):
        settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'), ('fr', 'Francais'))
        settings.FALLBACK = 'en'

    def test_duplicate_content(self, client):
        """ two content objects for the same language 
             cannot point to the same node """
        root = Node.root()
        child1 = root.add("n1")
        Type1(node=child1, language="nl").save()
        pytest.raises(NodeInUse, lambda: child1.set(Type1(language="nl").save()))

    def test_duplicate_content_different_languages(self, client):
        """ two content objects for different languages
             can point to the same node """
        root = Node.root()
        child1 = root.add("n1")
        Type1(node=child1, language="nl").save()
        child1.set(Type1(language="fr").save())

    def test_node_content(self, client):
        """ get the actual content instance through the node """
        root = Node.root()
        child1 = root.add("n1")
        c1 = Type1(node=child1)
        c1.save()
        child2 = root.add("n2")
        c2 = Type2(node=child2)
        c2.save()

        assert child1.content() == c1
        assert child2.content() == c2

    def test_node_set(self, client):
        """ test the node.set method """
        root = Node.root()
        child1 = root.add("n1")
        c1 = Type1()
        c1.save()
        child1.set(c1)
        c1 = Type1.objects.get(pk=c1.pk)  ## get updated state
        assert child1.content() == c1
        assert c1.node == child1

    def test_node_set_base(self, client):
        """ test the node.set method  with Content instance """
        root = Node.root()
        child1 = root.add("n1")
        c1 = Type1()
        c1.save()
        child1.set(c1.content_ptr)

        assert child1.content() == c1

    def test_node_set_replace(self, client):
        """ test the node.set method """
        root = Node.root()
        child1 = root.add("n1")
        c1 = Type1()
        c1.save()
        child1.set(c1)
        c2 = Type2()
        c2.save()
        old = child1.set(c2, replace=True)

        assert child1.content() == c2
        assert old == c1

    def test_node_set_inuse(self, client):
        """ a node can not hold two content items """
        root = Node.root()
        child1 = root.add("n1")
        c1 = Type1()
        c1.save()
        child1.set(c1)
        c2 = Type2()
        c2.save()
        pytest.raises(NodeInUse, child1.set, c2)

    def test_content_default(self, client):
        """ test defaults on new content """
        c1 = Type1()
        c1.save()
        assert c1.created
        assert c1.modified
        assert c1.publication
        assert c1.expire > timezone.now()
        assert not c1.navigation

    def test_content_default_update(self, client):
        """ test defaults on updated content """
        c1 = Type1()
        c1.save()
        created = c1.created
        modified = c1.modified
        c1.save()
        assert c1.modified > modified
        assert c1.created == created

    def test_absolute_url(self, client):
        """ the absolute url for a content object is that of its node """
        root = Node.root()
        n = root.add("path").add("sub")
        c1 = Type1(node=n).save()
        assert c1.get_absolute_url() == n.get_absolute_url()

    def test_absolute_url_unattached(self, client):
        """ the absolute url for unattached content is None """
        c1 = Type1().save()
        assert c1.get_absolute_url() is None

    ## copy/paste

    def test_copy_content_simple(self, client):
        """ Standard content copy. """
        c1 = Type1(title="hello", state="visible", t1field="orig").save()
        c2 = c1.copy()
        assert c1 != c2
        assert c1.title == c2.title
        assert c1.state == c2.state
        assert c1.t1field == c2.t1field

        c2.t1field = "copy"
        c2.save()

        ## verify the inheritance magic works as expected
        bases = Content.objects.all().order_by("id")
        assert bases.count() == 2
        orig = bases[0]
        copy = bases[1]

        assert orig != copy
        assert orig.type1 != copy.type1

        t1s = Type1.objects.all()
        assert t1s[0].t1field != t1s[1].t1field

    def test_copy_content_owner(self, client):
        """ verify the owner (foreign key) gets copied """
        ## Should current user become new owner? XXX
        owner = User.objects.get_or_create(username="owner")[0]
        c1 = Type1(title="hello", owner=owner).save()
        c2 = c1.copy()
        assert c1 != c2
        assert c1.owner == c2.owner

    def test_copy_content_m2m(self, client):
        """ m2m relations need special handling """
        m2m1 = TypeM2M().save()
        m2m2 = TypeM2M().save()
        c1 = TypeM2M().save()

        c1.m2m = [m2m1, m2m2]

        c2 = c1.copy()

        assert set(c2.m2m.all()) == set((m2m1, m2m2))

    def test_copy_content_unique(self, client):
        """ m2m relations need special handling """
        uniek = TypeUnique(uniek="one of a kind").save()

        pytest.raises(ContentCopyFailed, uniek.copy)

    def test_copy_content_not_copyable(self, client):
        """ m2m relations need special handling """
        not_copyable = Type1()
        not_copyable.copyable = False

        pytest.raises(ContentCopyNotSupported, not_copyable.copy)

    def test_copy_content_node(self, client):
        """ copy a node and its content """
        root = Node.root()
        n = root.add("content")
        c = Type1(title="c on n", node=n).save()

        n2, success, failed = root.paste(n, copy=True)
        assert n2.content() != n.content()
        assert n2.content().title == c.title
        assert n2.content().node != n

    def test_copy_content_node_recursive(self, client):
        root = Node.root()
        sub = root.add("sub")
        Type1(title="content on sub", node=sub).save()
        subc1 = sub.add("c1")
        Type1(title="content on sub/c1", node=subc1).save()
        subc2 = sub.add("c2")
        Type1(title="content on sub/c2", node=subc2).save()

        sub2, success, failed = root.paste(sub, copy=True)
        assert len(sub2.children()) == 2
        assert sub2.content() != sub.content()
        assert sub2.content().title == "content on sub"

        assert sub2.child("c1").content() != subc1.content()
        assert sub2.child("c1").content().title == "content on sub/c1"
        assert sub2.child("c2").content() != subc2.content()
        assert sub2.child("c2").content().title == "content on sub/c2"

    def test_copy_content_node_unique(self, client):
        root = Node.root()
        sub = root.add("sub")
        TypeUnique(title="content on sub", node=sub).save()

        sub2, success, failed = root.paste(sub, copy=True)
        assert len(root.children()) == 1
        assert len(success) == 0
        assert len(failed) == 1

    def test_copy_content_node_unique_sub(self, client):
        root = Node.root()
        sub = root.add("sub")
        Type1(title="content on sub", node=sub).save()
        subc1 = sub.add("c1")
        TypeUnique(uniek="unique content on sub/c1", node=subc1).save()
        subc2 = sub.add("c2")
        Type1(title="content on sub/c2", node=subc2).save()

        subunique = subc1.add("subunique")

        sub2, success, failed = root.paste(sub, copy=True)
        assert len(sub2.children()) == 1
        assert Node.get(sub2.path + "/c1/subunique") is None
        assert len(success) == 2
        assert len(failed) == 1

    ## translation tests
    def test_translations(self, client):
        root = Node.root()
        sub = root.add("sub")
        Type1(title="EN content on sub", node=sub, language="en").save()
        Type1(title="NL content on sub", node=sub, language="nl").save()

        assert sub.content(language="en").title == "EN content on sub"
        assert sub.content(language="nl").title == "NL content on sub"
        assert sub.primary_content()
        assert not sub.content(language="fr")

    def test_translation_any(self, client):
        root = Node.root()
        sub = root.add("sub")
        Type1(title="Any content on sub", node=sub, language="any").save()

        assert sub.content(language="en").title == "Any content on sub"
        assert sub.content(language="nl").title == "Any content on sub"
        assert sub.primary_content()

    def test_translation_specific_with_any(self, client):
        """ a specific match and an any match """
        root = Node.root()
        sub = root.add("sub")
        Type1(title="NL content on sub", node=sub, language="nl").save()
        Type1(title="Any content on sub", node=sub, language="any").save()

        assert sub.content(language="en").title == "Any content on sub"
        assert sub.content(language="nl").title == "NL content on sub"
        assert sub.primary_content()

    def xtest_translations_duplicate(self, client):
        root = Node.root()
        sub = root.add("sub")
        Type1(title="EN content on sub", node=sub, language="en").save()
        Type1(title="NL content on sub", node=sub, language="en").save()

        assert sub.content(language="en").title == "EN content on sub"
        assert sub.content(language="nl").title == "NL content on sub"
        assert sub.primary_content()
        assert not sub.content(langauge="fr")
