from .test_spoke import BaseLocalRegistry
from .models import Type1, Type1Type
from wheelcms_axle.node import Node

from django.utils import timezone
from datetime import timedelta

class TestNodeManager(BaseLocalRegistry):
    """
        Test the Node query Manager which provides methods to find
        public (published, not expired) and attached content
    """
    types = (Type1Type, )

    def setup_nodes(self):
        """ A mix of attached/unattached nodes, all unpublished """
        root = Node.root()
        _ = Type1(node=root.add("type1")).save()
        _ = Type1(node=root.add("attached")).save()
        i3 = root.add("unattached")
        _ = Type1(node=i3.add("attached-on-unattached")).save()

    def test_all_empty(self, client):
        """ no nodes at all """
        all = Node.objects.all()
        assert all.count() == 0

    def test_all(self, client):
        """ 5 nodes """
        self.setup_nodes()
        all = Node.objects.all()
        assert all.count() == 5

    def test_public_attached(self, client):
        """ 3 attached nodes """
        self.setup_nodes()
        attached = Node.objects.attached()
        assert attached.count() == 3

    def test_public_none(self, client):
        """ no (by default) published nodes """
        self.setup_nodes()
        public = Node.objects.public()
        assert public.count() == 0

    def test_public_publish(self, client):
        """ published without explicit expire/publication """
        Type1(node=Node.root(), state="published",
              expire=None, publication=None).save()
        public = Node.objects.public()
        assert public.count() == 1
        assert public[0] == Node.root()

    def test_public_expire(self, client):
        """ published with explicit expire """
        now = timezone.now()
        Type1(node=Node.root(), state="published",
              expire=now + timedelta(hours=1), publication=None).save()
        public = Node.objects.public()
        assert public.count() == 1
        assert public[0] == Node.root()

    def test_public_publication(self, client):
        """ published with explicit publication date """
        now = timezone.now()
        Type1(node=Node.root(), state="published",
              expire=None, publication=now - timedelta(hours=1)).save()
        public = Node.objects.public()
        assert public.count() == 1
        assert public[0] == Node.root()

    def test_public_past_expire(self, client):
        """ published content past expiration """
        now = timezone.now()
        Type1(node=Node.root(), state="published",
              expire=now - timedelta(hours=1), publication=None).save()
        public = Node.objects.public()
        assert public.count() == 0

    def test_public_before_publication(self, client):
        """ published content before publication """
        now = timezone.now()
        Type1(node=Node.root(), state="published",
              expire=None, publication=now + timedelta(hours=1)).save()
        public = Node.objects.public()
        assert public.count() == 0

    def test_children(self, client):
        """ Direct children of a given node """
        root = Node.root()
        a = root.add("a")
        a1 = a.add("a1")
        a2 = a.add("a2")
        a11 = a1.add("a11")

        c = Node.objects.all().children(a)
        assert c.count() == 2
        assert set(n.path for n in c) == set(("/a/a1", "/a/a2"))

    def test_offspring(self, client):
        """ children and their offspring """
        root = Node.root()
        a = root.add("a")
        a1 = a.add("a1")
        a2 = a.add("a2")
        a11 = a1.add("a11")

        c = Node.objects.all().offspring(a)
        assert c.count() == 3
        assert set(n.path for n in c) == set(("/a/a1", "/a/a2", "/a/a1/a11"))
