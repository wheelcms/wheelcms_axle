import mock

from wheelcms_axle.utils import generate_slug

class TestSlug(object):
    def test_empty(self):
        assert generate_slug('', default='foo') == 'foo'

    def test_maxlength(self):
        assert len(generate_slug('hello world', max_length=1)) == 1

    def test_duplicate_plus_dash(self):
        assert generate_slug('foo--- -- - -- bar') == 'foo-bar'

    def test_allowed(self):
        assert generate_slug("abcdef", allowed="a") == "a"

    def test_stopwords(self):
        with mock.patch("wheelcms_axle.stopwords.stopwords") as swmock:
            swmock.get.return_value = ["foo", "bar"]
            assert generate_slug("foo blah bar") == "blah"
