import mimetypes
import os
import datetime

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

from .registry import Registry

from .node import Node


def far_future():
    """ default expiration is roughly 20 years from now """
    return timezone.now() + datetime.timedelta(days=(20*365+8))


class ContentClass(models.Model):
    name = models.CharField(max_length=256, blank=False)


class ContentBase(models.Model):
    CLASSES = ()

    node = models.OneToOneField(Node, related_name="contentbase", null=True)
    title = models.CharField(max_length=256, blank=False)
    created = models.DateTimeField(blank=True, null=True)
    modified = models.DateTimeField(blank=True, null=True)
    publication = models.DateTimeField(blank=True, null=True,
                                       default=timezone.now)
    expire = models.DateTimeField(blank=True, null=True,
                                  default=far_future)

    ## workflow determines possible states and their meaning
    state = models.CharField(max_length=30, blank=True)

    template = models.CharField(max_length=255, blank=True)

    ## one could argue that this can be a property on a node
    navigation = models.BooleanField(default=False)

    meta_type = models.CharField(max_length=20)

    ## can be null for now, should move to null=False eventually
    owner = models.ForeignKey(User, null=True)

    ## class..
    classes = models.ManyToManyField(ContentClass, related_name="content")

    class Meta:
        abstract = True

    def save(self, *a, **b):
        ## XXX can this be replaced by a default on meta_type?
        mytype = self.__class__.__name__.lower()
        self.meta_type = mytype
        self.modified = timezone.now()
        if self.created is None:
            self.created = timezone.now()
        ## find associated spoke to find workflow default?
        ## if not self.state and state not in b, get default from spoke
        if not self.state and 'state' not in b:
            self.state = self.spoke().workflow().default

        super(ContentBase, self).save(*a, **b)
        for klass in self.CLASSES:
            self.classes.add(ContentClass.objects.get_or_create(name=klass)[0])
        return self  ## foo = x.save() is nice

    def content(self):
        if self.meta_type:
            return getattr(self, self.meta_type)

    def spoke(self):
        """ return the spoke for this model """
        return type_registry.get(self.meta_type)(self)

    @classmethod
    def get_name(cls):
        ## include app_label ? #486
        return cls._meta.object_name.lower()

    def __unicode__(self):
        try:
            return u"%s connected to node %s: %s" % \
                    (self.meta_type, self.node, self.title)
        except Node.DoesNotExist:
            return u"Unconnected %s: %s" % (self.meta_type, self.title)


WHEEL_CONTENT_BASECLASS = ContentBase


class Content(WHEEL_CONTENT_BASECLASS):
    pass


class ClassContentManager(models.Manager):
    def __init__(self, name):
        self.name = name

    def get_query_set(self):
        return ContentClass.objects.get_or_create(name=self.name)[0].content.all()


class FileContent(Content):
    FILECLASS = "wheel.file"
    CLASSES = Content.CLASSES + (FILECLASS, )

    objects = models.Manager()
    instances = ClassContentManager(FILECLASS)

    content_type = models.CharField(blank=True, max_length=256)
    filename = models.CharField(blank=True, max_length=256)

    class Meta(Content.Meta):
        abstract = True


    def save(self, *a, **b):
        """
            Intercept save, fill in defaults for filename and mimetype if
            not explicitly set
        """
        if not self.filename:
            self.filename = self.storage.name or self.title
            ## guess extension if missing?
        self.filename = os.path.basename(self.filename)

        if not self.content_type:
            type, encoding = mimetypes.guess_type(self.filename)
            if type is None:
                type = "application/octet-stream"
            self.content_type = type
        return super(FileContent, self).save(*a, **b)


class ImageContent(FileContent):
    IMAGECLASS = "wheel.image"
    CLASSES = FileContent.CLASSES + ("wheel.image", )

    objects = models.Manager()
    instances = ClassContentManager(IMAGECLASS)

    class Meta(FileContent.Meta):
        abstract = True


class TypeRegistry(dict):
    def register(self, t):
        self[t.name()] = t


type_registry = Registry(TypeRegistry())
