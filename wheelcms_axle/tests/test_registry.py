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
