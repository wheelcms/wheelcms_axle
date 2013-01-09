from django.db import models, IntegrityError
from django.utils import timezone

import re
import datetime

class NodeException(Exception):
    pass

class DuplicatePathException(NodeException):
    pass

class InvalidPathException(NodeException):
    pass

class NodeInUse(NodeException):
    pass

class NodeBase(models.Model):
    ROOT_PATH = ""
    ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    MAX_PATHLEN = 20
    POSITION_INTERVAL = 100

    validpathre = re.compile("^[%s]{1,%d}$" % (ALLOWED_CHARS, MAX_PATHLEN))

    path = models.CharField(max_length=MAX_PATHLEN, blank=False, unique=True)
    position = models.IntegerField(default=0)


    class Meta:
        abstract = True

    def content(self):
        try:
            return self.contentbase.content()
        except Content.DoesNotExist:
            return None

    @classmethod
    def get(cls, path):
        """ retrieve node directly by path. Returns None if not found """
        try:
            return cls.objects.get(path=path)
        except cls.DoesNotExist:
            if path == "":
                return cls.root()

            return None

    def set(self, content, replace=False):
        """
            Set content on the node, optionally replacing existing
            content. This is a more friendly way of setting the node
            on a Content directly
        """
        ## just to be sure, in case it's of type Content in stead of
        ## subclass
        content = content.content()

        old = None
        try:
            if self.contentbase:
                if replace:
                    old = self.content()
                    old.node = None
                    old.save()
                else:
                    raise NodeInUse()
        except Content.DoesNotExist:
            pass

        self.contentbase = content #.content_ptr  # XXX is _ptr documented?
        #content.node = self
        content.save()
        self.save()

        return old

    @classmethod
    def root(cls):
        return cls.objects.get_or_create(path=cls.ROOT_PATH)[0]

    def isroot(self):
        return self.path == self.ROOT_PATH

    def add(self, path, position=-1, after=None, before=None):
        """ handle invalid paths (invalid characters, empty, too long) """
        ## lowercasing is the only normalization we do
        path = path.lower()

        if not self.validpathre.match(path):
            raise InvalidPathException(path)

        children = self.children()
        positions = (c.position for c in self.children())

        if after:
            try:
                afterafter_all = self.childrenq(position__gt=after.position,
                                            order="position")
                afterafter = afterafter_all.get()
                position = (after.position + afterafter.position) / 2
                if position == after.position:
                    ## there's a conflict. the new position will be 
                    ## "after.position + POSITION_INTERVAL", renumber
                    ## everything else
                    position = after.position + self.POSITION_INTERVAL
                    for i, n in enumerate(afterafter_all):
                        n.position = position + ((i + 1) * self.POSITION_INTERVAL)
                        n.save()
                    # XXX self.debug("repositioning children")
            except Node.DoesNotExist:
                ## after is the last childnode
                position = after.position + self.POSITION_INTERVAL
        elif before:
            try:
                beforebefore_all = self.childrenq(position__lt=before.position,
                                            order="position")
                beforebefore = beforebefore_all.latest("position")
                position = (before.position + beforebefore.position) / 2
                if position == beforebefore.position:
                    ## there's a conflict. the new position will be 
                    ## "before.position", renumber before and everything
                    ## else after it.
                    position = before.position
                    everything_after = self.childrenq(
                                           position__gte=before.position,
                                           order="position")
                    for i, n in enumerate(everything_after):
                        n.position = position + ((i + 1) *
                                                 self.POSITION_INTERVAL)
                        n.save()
                    # XXX self.debug("repositioning children")
            except Node.DoesNotExist:
                ## before is the first childnode
                position = before.position - self.POSITION_INTERVAL
        elif position == -1:
            if children.count():
                position = max(positions) + self.POSITION_INTERVAL
            else:
                position = 0

        child = self.__class__(path=self.path + "/" + path,
                               position=position)
        try:
            child.save()
            # XXX child.info(action=create)
        except IntegrityError:
            raise DuplicatePathException(path)
        return child

    def parent(self):
        """ return the parent for this node """
        if self.isroot():
            return self
        parentpath, mypath = self.path.rsplit("/", 1)
        parent = self.__class__.objects.get(path=parentpath)
        return parent

    def childrenq(self, order="position", **kw):
        """ return the raw query for children """
        return self.__class__.objects.filter(
                  path__regex="^%s/[%s]+$" % (self.path, self.ALLOWED_CHARS),
                  **kw
                  ).order_by(order)

    def children(self, order="position"):
        return self.childrenq(order=order)

    def slug(self):
        """ last part of self.path """
        return self.path.rsplit("/", 1)[-1]

    def set_slug(self, slug):
        """ change the slug """
        newpath = self.path.rsplit("/", 1)[0] + "/" + slug
        if Node.objects.filter(path=newpath).count():
            raise DuplicatePathException(newpath)
        self.path = newpath
        self.save()

    def __unicode__(self):
        """ readable representation """
        return u"path %s pos %d" % (self.path or '/', self.position)

WHEEL_NODE_BASECLASS = NodeBase
class Node(WHEEL_NODE_BASECLASS):
    pass

def far_future():
    """ default expiration is roughly 20 years from now """
    return timezone.now() + datetime.timedelta(days=(20*365+8))

class ContentBase(models.Model):
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

    class Meta:
        abstract = True

    def save(self, *a, **b):
        ## XXX can this be replaced by a default on meta_type?
        mytype = self.__class__.__name__.lower()
        self.meta_type = mytype
        self.modified = timezone.now()
        if self.created is None:
            self.created = timezone.now()
        super(ContentBase, self).save(*a, **b)

    def content(self):
        if self.meta_type:
            return getattr(self, self.meta_type)

    def __unicode__(self):
        try:
            return u"%s connected to node %s: %s" % \
                    (self.meta_type, self.node, self.title)
        except Node.DoesNotExist:
            return u"Unconnected %s: %s" % (self.meta_type, self.title)

WHEEL_CONTENT_BASECLASS = ContentBase

class Content(WHEEL_CONTENT_BASECLASS):
    pass


class TypeRegistry(dict):
    def register(self, t):
        self[t.name()] = t


class Registry(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def set(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, k):
        return getattr(self.wrapped, k)


type_registry = Registry(TypeRegistry())
