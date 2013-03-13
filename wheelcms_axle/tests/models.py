from wheelcms_axle.content import Content, FileContent, ImageContent
from wheelcms_axle.spoke import Spoke, action
from wheelcms_axle.content import type_registry

from django.db import models

class Type1(Content):
    t1field = models.TextField(null=True, blank=True)


class Type1Type(Spoke):
    model = Type1

    @action
    def hello(self, handler, request, action):
        return ("Hello", request, handler, self, action)

class Type2(Content):
    pass


class Type2Type(Spoke):
    model = Type2


class TestFile(FileContent):
    storage = models.FileField(upload_to="files", blank=False)


class TestFileType(Spoke):
    model = TestFile
    children = ()

class OtherTestFile(FileContent):
    storage = models.FileField(upload_to="files", blank=False)


class OtherTestFileType(Spoke):
    model = OtherTestFile
    children = ()


class TestImage(ImageContent):
    storage = models.ImageField(upload_to="images", blank=False)


class TestImageType(Spoke):
    model = TestImage
    children = ()

class OtherTestImage(ImageContent):
    storage = models.ImageField(upload_to="images", blank=False)


class OtherTestImageType(Spoke):
    model = OtherTestImage
    children = ()


type_registry.register(Type1Type)
type_registry.register(Type2Type)
type_registry.register(TestFileType)
type_registry.register(TestImageType)
type_registry.register(OtherTestFileType)
type_registry.register(OtherTestImageType)

from wheelcms_axle.content import TypeRegistry

class TestTypeRegistry(TypeRegistry):
    """
        A type registry without HayStack registration
    """
    def register(self, t):
        self[t.name()] = t

