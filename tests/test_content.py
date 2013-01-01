from wheelcms_axle.models import Node, NodeInUse
from wheelcms_axle.tests.models import Type1, Type2

from django.db import IntegrityError
from django.utils import timezone

import pytest

class TestContent(object):
    """ Test content / content-node related stuff """

    def test_duplicate_content(self, client):
        """ two content objects cannot point to the same node """
        root = Node.root()
        child1 = root.add("n1")
        Type1(node=child1).save()
        pytest.raises(IntegrityError, lambda: Type1(node=child1).save())

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
