"""
    Test the standalone template registry
"""
from wheelcms_axle.templates import TemplateRegistry
from wheelcms_axle.tests.models import Type1
from wheelcms_axle.tests.models import Type1Type, Type2Type

class TestTemplateRegistry(object):
    """ Test the registry """
    def setup(self):
        """ a registry to test on """
        self.reg = TemplateRegistry()

    def test_empty(self):
        """ if it's empty """
        assert self.reg.get(Type1) is None

    def test_single_nodefault(self):
        """ A single entry without default """
        self.reg.register(Type1Type, "foo/bar", "foo bar")
        assert self.reg.get(Type1) == [("foo/bar", "foo bar")]
        assert self.reg.defaults.get(Type1) is None

    def test_double(self):
        """ Two entries for a Spoke """
        self.reg.register(Type1Type, "foo/bar", "foo bar")
        self.reg.register(Type1Type, "foo/bar2", "foo bar2")
        assert self.reg.get(Type1) == [("foo/bar", "foo bar"),
                                  ("foo/bar2", "foo bar2")]

    def test_empty_default(self):
        """ An empty registry has no defaults """
        assert self.reg.defaults.get(Type1) is None

    def test_single_default(self):
        """ It does if you set one """
        self.reg.register(Type1Type, "foo/bar", "foo bar", default=True)
        assert self.reg.get(Type1) == [("foo/bar", "foo bar")]
        assert self.reg.defaults.get(Type1) == "foo/bar"

    def test_valid(self):
        """ Registered templates are valid """
        self.reg.register(Type1Type, "foo/bar", "foo bar")
        assert self.reg.valid_for_model(Type1, "foo/bar")

    def test_invalid(self):
        """ Unregistered aren't, not even when registered on different Spoke """
        self.reg.register(Type1Type, "foo/bar", "foo bar")
        self.reg.register(Type2Type, "foo/bar2", "foo bar2")
        assert not self.reg.valid_for_model(Type1, "foo/bar2")
