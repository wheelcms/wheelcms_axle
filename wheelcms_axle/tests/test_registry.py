from django.db import models

from ..content import TypeRegistry


class M1(models.Model):
    """ mocked model """
    pass

class M2(models.Model):
    """ mocked model """
    pass

class M3(M1):
    """ mocked model """
    pass

class A(object):
    """ mocked type """
    model = M1
    add_to_index = False

    @classmethod
    def name(cls):
        return 'A'

    @classmethod
    def index(cls):
        return ''

class B(A):
    """ mocked type """
    model = M3
    add_to_index = False

    @classmethod
    def name(cls):
        return 'B'

class TestTypeRegistry(object):
    """
        Test the registries extend functionality
    """
    def test_extends_none(self, client):
        """ no special extending """
        r = TypeRegistry()
        r.register(A)

        assert r.extenders(M1) == []

    def test_extends_direct_match(self, client):
        """ a direct extension match """
        r = TypeRegistry()
        r.register(A, extends=M2)

        assert r.extenders(M2) == [A]

    def test_extends_indirect_match(self, client):
        """ indirect match through base """
        r = TypeRegistry()
        r.register(A, extends=models.Model)

        assert r.extenders(M2) == [A]

    def test_extends_multi(self, client):
        """ A extends multiple models """
        r = TypeRegistry()
        r.register(B)
        r.register(A, extends=[M2, M3])


        assert r.extenders(M2) == [A]
        assert r.extenders(M3) == [A]

    def test_extends_multi2(self, client):
        """ different types extend same model """
        r = TypeRegistry()
        r.register(A, extends=[M2])
        r.register(B, extends=[M2])


        assert set(r.extenders(M2)) == set([A, B])

from wheelcms_axle.registries.core_registry import CoreRegistry
from wheelcms_axle.registries.registry import Registry

class TestCoreRegistry(object):
    """ Test the core registry, that holds other registries """

    def test_default(self):
        """ default empty init """
        r = CoreRegistry()
        assert r.reg == {}

    def test_set(self):
        """ using the set() method """
        r = CoreRegistry()
        r.set('a', 'b')
        assert r.a == 'b'

    def test_setattr(self):
        """ attribute assignment """
        r = CoreRegistry()
        r.a = 'b'
        assert r.a == 'b'

class TestRegistry(object):
    """ A registry actually proxies """

    def test_wrap(self):
        """ default wrapping """
        w = Registry('a')
        assert w == 'a'

    def test_wrap_proxy(self):
        """ attribute access is proxied """
        l = []
        w = Registry(l)
        assert w.append == l.append

    def test_set_override(self):
        """ Wrapped content can be replaced """
        w = Registry('a')
        w.set('b')
        assert w == 'b'
        assert w.__wrapped__ == 'b'

    def test_iter(self):
        """ __iter__ works """
        w = Registry(iter("abc"))
        assert list(w) == list("abc")
