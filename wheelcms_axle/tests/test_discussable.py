from .test_spoke import BaseLocalRegistry
from .models import Type1, Type2, Type1Type, Type2Type

class TestDiscussable(BaseLocalRegistry):
    types = (Type1Type, Type2Type)

    def test_default_enabled(self, client):
        t = Type1().save()
        spoke = Type1Type(t)
        assert spoke.can_discuss()

    def test_default_disabled(self, client):
        t = Type2().save()
        spoke = Type2Type(t)
        assert not spoke.can_discuss()

    def test_default_enabled_explicit_off(self, client):
        t = Type1(discussable=False).save()
        spoke = Type1Type(t)
        assert not spoke.can_discuss()

    def test_default_enabled_explicit_on(self, client):
        t = Type1(discussable=True).save()
        spoke = Type1Type(t)
        assert spoke.can_discuss()

    def test_default_disabled_explicit_off(self, client):
        t = Type2(discussable=False).save()
        spoke = Type2Type(t)
        assert not spoke.can_discuss()

    def test_default_disabled_explicit_on(self, client):
        t = Type2(discussable=True).save()
        spoke = Type2Type(t)
        assert spoke.can_discuss()
