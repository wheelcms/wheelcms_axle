from wheelcms_axle.node import Node
from django.utils import translation

class TestRootNode(object):
    def setup(self):
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')
        settings.FALLBACK = False

    def xtest_disabled(self, client):
        """ multi language support disabled """
        pass

    def test_language_path(self, client):
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')
        translation.activate('en')
        root = Node.root()
        assert root.path == ''

    def test_non_supported_language(self, client):
        """ a non-supported language, no fallback """
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')
        translation.activate('de')
        root = Node.root()
        assert root is None

    def test_default(self, client):
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')
        settings.FALLBACK = 'en'
        root = Node.root()
        assert root.path == ''

    ## root cannot be renamed

class TestNode(object):
    def setup(self):
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')

    def test_node(self, client):
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        en_child = Node.get("/child")
        assert en_child == child
        assert en_child.path == "/child"

    def test_node_slug_language(self, client):
        """ A node with different slugs for different languages """
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        # import pytest; pytest.set_trace()
        child.rename("kind", language="nl")
        child.rename("enfant", language="fr")

        translation.activate('nl')
        nl_child = Node.get("/kind")
        assert nl_child == child
        assert nl_child.path == "/kind"

    def test_node_slug_offspring_language(self, client):
        """ A node with different slugs for different languages,
            with children"""
        translation.activate('en')
        root = Node.root()
        child = root.add("child")
        child1 = child.add("grandchild1")
        child2 = child.add("grandchild2")

        child.rename("kind", language="nl")
        child2.rename("kleinkind2")

        translation.activate('nl')
        nl_child2 = Node.get("/kind/kleinkind2")
        assert nl_child2 == child2
        assert nl_child2.path == "/kind/kleinkind2"

        nl_child1 = Node.get("/kind/grandchild1")
        assert nl_child1 == child1
        assert nl_child1.path == "/kind/grandchild1"
    ## test rename

class TestContent(object):
    pass

