from wheelcms_axle.content import Content, FileContent, ImageContent
from wheelcms_axle.spoke import Spoke, action, FileSpoke
from wheelcms_axle.content import type_registry

from django.db import models

class Type1(Content):
    t1field = models.TextField(null=True, blank=True)


class Type1Type(Spoke):
    model = Type1
    discussable = True

    @action
    def hello(self, handler, request, action):
        return ("Hello", request, handler, self, action)

class Type2(Content):
    pass


class Type2Type(Spoke):
    model = Type2
    discussable = False


class TestFile(FileContent):
    storage = models.FileField(upload_to="files", blank=False)


class TestFileType(FileSpoke):
    model = TestFile
    children = ()

class OtherTestFile(FileContent):
    storage = models.FileField(upload_to="files", blank=False)


class OtherTestFileType(FileSpoke):
    model = OtherTestFile
    children = ()


class TestImage(ImageContent):
    storage = models.ImageField(upload_to="images", blank=False)


class TestImageType(FileSpoke):
    model = TestImage
    children = ()

class OtherTestImage(ImageContent):
    storage = models.ImageField(upload_to="images", blank=False)


class OtherTestImageType(FileSpoke):
    model = OtherTestImage
    children = ()

class TypeM2M(Content):
    m2m = models.ManyToManyField("self")

class TypeM2MType(Spoke):
    model = TypeM2M

class TypeUnique(Content):
    uniek = models.TextField(unique=True)

class TypeUniqueType(Spoke):
    model = TypeUnique

type_registry.register(Type1Type)
type_registry.register(Type2Type)
type_registry.register(TestFileType)
type_registry.register(TestImageType)
type_registry.register(OtherTestFileType)
type_registry.register(OtherTestImageType)
type_registry.register(TypeM2MType)
type_registry.register(TypeUniqueType)

from wheelcms_axle.content import TypeRegistry

class TestTypeRegistry(TypeRegistry):
    """
        A type registry without HayStack registration
    """
    def register(self, t):
        self[t.name()] = t

from wheelcms_axle.models import Configuration as BaseConfiguration
from wheelcms_axle.registries.configuration import configuration_registry

class Configuration(models.Model):
    main = models.ForeignKey(BaseConfiguration, related_name="testconf")
    value = models.TextField(blank=True)

configuration_registry.register("testconf", "ConfTest", Configuration, None)

