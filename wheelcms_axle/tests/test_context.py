import mock

from wheelcms_axle.context import ContentContext

class TestContext(object):
    contextclass = ContentContext

    def test_init(self):
        mocked = mock.MagicMock()
        context = self.contextclass(mocked)
        assert context.content == mocked

    def test_title(self):
        mocked = mock.MagicMock()
        context = self.contextclass(mocked)
        assert context.title() == mocked.instance.title

    def test_url(self):
        mocked = mock.MagicMock()
        context = self.contextclass(mocked)
        assert context.url() == mocked.instance.get_absolute_url()

    def test_getattr(self):
        """ if an attribute does not exist, perform a getattr on
            content.instance """
        mocked = mock.MagicMock()
        context = self.contextclass(mocked)
        assert context.somethingrandom == mocked.instance.somethingrandom
