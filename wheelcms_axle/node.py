import re

from django.db import models, IntegrityError
from django.core.urlresolvers import reverse


class NodeException(Exception):
    """ Base class for all Node exceptions """

class DuplicatePathException(NodeException):
    """ the path is already in use """

class InvalidPathException(NodeException):
    """ The path contains non-valid chars or is too short """

class NodeInUse(NodeException):
    """ the node already has content attached to it """

class CantRenameRoot(NodeException):
    """ the root's path is "" which cannot be changed """

class NodeNotFound(NodeException):
    """ raised if a node is not found """

from django.db.models.query import QuerySet
from django.utils import timezone
from django.db.models import Q

class NodeQuerySet(QuerySet):
    def children(self, node):
        """ only return direct children """
        return self.filter(
                  path__regex="^%s/[%s]+$" % (node.path, Node.ALLOWED_CHARS),
                  )

    def offspring(self, node):
        """ children, grandchildren, etc """
        return self.filter(
                  path__regex="^%s/[%s]+" % (node.path, Node.ALLOWED_CHARS),
                  )

    def attached(self):
        return self.filter(contentbase__isnull=False)

    def public(self):
        now = timezone.now()
        return (self.attached().filter(
                Q(contentbase__publication__isnull=True)|
                Q(contentbase__publication__lte=now),
                Q(contentbase__expire__isnull=True)|
                Q(contentbase__expire__gte=now),
                contentbase__state='published'))


class NodeManager(models.Manager):
    def get_query_set(self):
        """ Return the NodeQuerySet that supports additional filters """
        return NodeQuerySet(self.model)

    def attached(self):
        return self.all().attached()

    def public(self):
        return self.all().public()

    def children(self, node):
        return self.all().children(node)

    def offspring(self, node):
        return self.all().offspring(node)

    def visible(self, user):
        """
            XXX TODO: when is content visible? May be even more
            complex when roles are supported
        """


class NodeBase(models.Model):
    ROOT_PATH = ""
    ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    MAX_PATHLEN = 100
    POSITION_INTERVAL = 100

    validpathre = re.compile("^[%s]{1,%d}$" % (ALLOWED_CHARS, MAX_PATHLEN))

    path = models.CharField(max_length=1024, blank=False, unique=True)
    position = models.IntegerField(default=0)

    objects = NodeManager()

    class Meta:
        abstract = True

    def content(self):
        from .content import Content
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
        from .content import Content
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
        ## avoid updating last_modified
        content.save(update_lm=False)
        self.save()

        return old

    @classmethod
    def root(cls):
        return cls.objects.get_or_create(path=cls.ROOT_PATH)[0]

    def isroot(self):
        return self.path == self.ROOT_PATH

    def find_position(self, position=-1, after=None, before=None):
        children = self.children()
        positions = (c.position for c in self.children())

        if after:
            try:
                afterafter_all = self.childrenq(position__gt=after.position,
                                            order="position")[:1]
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
        return position

    def add(self, path, position=-1, after=None, before=None):
        """ handle invalid paths (invalid characters, empty, too long) """
        ## lowercasing is the only normalization we do
        path = path.lower()

        if not self.validpathre.match(path):
            raise InvalidPathException(path)

        position = self.find_position(position, after, before)

        child = self.__class__(path=self.path + "/" + path,
                               position=position)
        try:
            child.save()
        except IntegrityError:
            raise DuplicatePathException(path)
        return child

    def move(self, child, position=-1, after=None, before=None):
        """ move an existing child. This does not take into acount that the
            child already has a position in the child-order, but that shouldn't
            make a significant difference """
        position = self.find_position(position, after, before)
        child.position = position
        child.save()

    def remove(self, childslug):
        """ remove a child, recursively """
        child = self.child(childslug)
        if child is None:
            raise NodeNotFound(self.path + '/' + childslug)
        child.delete()
        recursive = Node.objects.filter(path__startswith=self.path + '/' +
                                                         childslug + '/')
        recursive.delete()

    def parent(self):
        """ return the parent for this node """
        if self.isroot():
            return self
        parentpath, mypath = self.path.rsplit("/", 1)
        parent = self.__class__.objects.get(path=parentpath)
        return parent

    def childrenq(self, order="position", **kw):
        """ return the raw query for children """
        return self.__class__.objects.children(self).order_by(order).filter(**kw)

    def children(self, order="position"):
        return self.childrenq(order=order)

    def child(self, slug):
        """ return a specific child by its slug """
        childpath = self.path + '/' + slug

        return self.get(childpath)

    def slug(self):
        """ last part of self.path """
        return self.path.rsplit("/", 1)[-1]

    def rename(self, slug):
        """ change the slug """
        if self.isroot():
            raise CantRenameRoot()

        newpath = self.path.rsplit("/", 1)[0] + "/" + slug
        if Node.objects.filter(path=newpath).count():
            raise DuplicatePathException(newpath)
        ## do something transactionish?
        for childs in Node.objects.filter(path__startswith=self.path + '/'):
            remainder = childs.path[len(self.path):]
            childs.path = newpath + remainder
            childs.save()
        self.path = newpath
        self.save()

    def get_absolute_url(self):
        ## strip any leading / since django will add that as well
        return reverse('wheel_main', kwargs={'instance':self.path.lstrip('/')})

    def __unicode__(self):
        """ readable representation """
        return u"path %s pos %d" % (self.path or '/', self.position)

WHEEL_NODE_BASECLASS = NodeBase
class Node(WHEEL_NODE_BASECLASS):
    pass
