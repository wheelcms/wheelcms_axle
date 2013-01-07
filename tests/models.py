from wheelcms_axle.models import Content
from wheelcms_spokes.models import formfactory, Spoke

from django.db import models

class Type1(Content):
    t1field = models.TextField(null=True, blank=True)


class Type1Type(Spoke):
    model = Type1


class Type2(Content):
    pass


class Type2Type(Spoke):
    model = Type2

from wheelcms_axle.models import type_registry

type_registry.register(Type1Type)
type_registry.register(Type2Type)
