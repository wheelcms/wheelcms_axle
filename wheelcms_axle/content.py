import mimetypes
import os
import datetime

from two.ol.util import classproperty

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models, IntegrityError
from django.conf import settings

from taggit.managers import TaggableManager

from .registry import Registry

from .node import Node

class ContentException(Exception):
    pass

class ContentCopyException(ContentException):
    pass

class ContentCopyNotSupported(ContentCopyException):
    pass

class ContentCopyFailed(ContentCopyException):
    pass

def far_future():
    """ default expiration is roughly 20 years from now """
    return timezone.now() + datetime.timedelta(days=(20*365+8))


class ContentClass(models.Model):
    name = models.CharField(max_length=256, blank=False)

    def __unicode__(self):
        return "Content class %s" % self.name


class ContentBase(models.Model):
    CLASSES = ()

    copyable = True

    node = models.ForeignKey(Node, related_name="contentbase", null=True)
    language = models.CharField(max_length=10, choices=(("any", "Any"),) + settings.CONTENT_LANGUAGES, blank=False)
    title = models.CharField(max_length=256, blank=False)
    description = models.TextField(blank=True, default="")
    created = models.DateTimeField(blank=True, null=True)
    modified = models.DateTimeField(blank=True, null=True)
    publication = models.DateTimeField(blank=True, null=True,
                                       default=timezone.now)
    expire = models.DateTimeField(blank=True, null=True,
                                  default=far_future)

    ## workflow determines possible states and their meaning
    state = models.CharField(max_length=30, blank=True)

    template = models.CharField(max_length=255, blank=True, default="")

    ## one could argue that this can be a property on a node
    navigation = models.BooleanField(default=False)

    meta_type = models.CharField(max_length=20)

    ## can be null for now, should move to null=False eventually
    owner = models.ForeignKey(User, null=True)

    ## class..
    classes = models.ManyToManyField(ContentClass, related_name="content",
                                     blank=True)

    tags = TaggableManager(blank=True)

    ## explicit comment enable/disable
    discussable = models.NullBooleanField(blank=True, null=True, default=None)

    class Meta:
        abstract = True

    def save(self, update_lm=True, *a, **b):
        mytype = self.__class__.__name__.lower()
        self.meta_type = mytype

        ## default does not seem to work as expected?
        if not self.language:
            self.language = settings.FALLBACK

        if update_lm or self.modified is None:
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

    def copy(self, node=None):
        """ create a copy, attach it to new node if specified.
            content is copyable by default, but special measures must
            be taken with ManyToMany fields and fields with a unique=True
            constraint.

            To disable copy support on a model set copyable = False
            (shouldn't this be defined at Spoke level? XXX)
        """
        if not self.copyable:
            raise ContentCopyNotSupported()

        c = self.__class__.objects.get(pk=self.pk)
        c.pk = c.id = None
        if node:
            c.node = node

        try:
            c.save()
        except IntegrityError as e:
            ## most likely a unique field
            raise ContentCopyFailed(e.args[0])

        for m2m in c._meta.many_to_many:
            setattr(c, m2m.name, getattr(self, m2m.name).all())
        return c

    def content(self):
        if self.meta_type:
            return getattr(self, self.meta_type)

    def spoke(self):
        """ return the spoke for this model """
        return type_registry.get(self.get_name())(self)

    @classproperty
    def classname(cls):
        return cls._meta.object_name.lower()

    @classmethod
    def get_name(cls):
        ## include app_label ? #486
        return "%s.%s" % (cls._meta.app_label.lower(), cls._meta.object_name.lower())

    def get_absolute_url(self):
        if self.node is None:
            return None
        return self.node.get_absolute_url(self.language)

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

    @classproperty
    def instances(cls):
        """ Since django 1.5, this is no longer a manager since
           'AttributeError: Manager isn't available; FileContent is abstract'
        """
        return ContentClass.objects.get_or_create(name=cls.FILECLASS)[0].content.all()

    # instances = ClassContentManager(FILECLASS)

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

    @classproperty
    def instances(cls):
        """ Since django 1.5, this is no longer a manager since
           'AttributeError: Manager isn't available; ImageContent is abstract'
        """
        return ContentClass.objects.get_or_create(name=cls.IMAGECLASS)[0].content.all()

    # instances = ClassContentManager(IMAGECLASS)
    caption = models.TextField(blank=True, default="")

    class Meta(FileContent.Meta):
        abstract = True

from haystack import exceptions, site

class TypeRegistry(dict):
    def __init__(self, *a, **b):
        super(TypeRegistry, self).__init__(*a, **b)
        self._extenders = {}

    def register(self, t, extends=None):
        """ register a type and the models it extends """
        self[t.name()] = t
        if extends:
            try:
                for e in extends:
                    self._extenders.setdefault(e, []).append(t)
            except TypeError: # not iterable
                self._extenders.setdefault(extends, []).append(t)

        if t.add_to_index:
            try:
                site.register(t.model, t.index())
            except exceptions.AlreadyRegistered:
                pass

    def extenders(self, model):
        """ find extenders for a given model """
        e = []
        e.extend(self._extenders.get(model, []))
        for m in model.__bases__:
            e.extend(self.extenders(m))
        return e

type_registry = Registry(TypeRegistry())
