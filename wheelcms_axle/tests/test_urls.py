from django.conf import settings
from django.core.urlresolvers import clear_url_caches

from ..node import Node

class Base(object):
    def setup(self):
        if hasattr(self, 'urls'):
            self._old_root_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = self.urls
            clear_url_caches()

    def teardown(self):
        if hasattr(self, '_old_root_urlconf'):
            settings.ROOT_URLCONF = self._old_root_urlconf
            clear_url_caches()


class TestInRoot(Base):
    urls = "wheelcms_axle.tests.urls_root"

    def test_rootnode(self, client):
        assert Node.root().get_absolute_url() == '/'

    def test_child_in_root(self, client):
        c = Node.root().add('foo')
        assert c.get_absolute_url() == '/foo/'

    def test_child_in_child(self, client):
        c = Node.root().add('foo').add('bar')
        assert c.get_absolute_url() == '/foo/bar/'


class TestInBlog(Base):
    urls = "wheelcms_axle.tests.urls_blog"

    def test_rootnode(self, client):
        assert Node.root().get_absolute_url() == '/blog/'

    def test_child_in_root(self, client):
        c = Node.root().add('foo')
        assert c.get_absolute_url() == '/blog/foo/'

    def test_child_in_child(self, client):
        c = Node.root().add('foo').add('bar')
        assert c.get_absolute_url() == '/blog/foo/bar/'


