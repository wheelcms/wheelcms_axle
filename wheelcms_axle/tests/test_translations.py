from wheelcms_axle.node import Node
from django.utils import translation

class TestRootNode(object):
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
        """ a non-supported language """
        from django.conf import settings
        settings.LANGUAGES = ('en', 'nl', 'fr')
        translation.activate('de')
        root = Node.root()
        assert root is None

    ## root cannot be renamed

class TestNode(object):
    pass
    ## test rename

class TestContent(object):
    pass

