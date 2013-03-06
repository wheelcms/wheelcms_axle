import re

from django.db import models, IntegrityError


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

class NodeBase(models.Model):
    ROOT_PATH = ""
    ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    MAX_PATHLEN = 40
    POSITION_INTERVAL = 100

    validpathre = re.compile("^[%s]{1,%d}$" % (ALLOWED_CHARS, MAX_PATHLEN))

    path = models.CharField(max_length=1024, blank=False, unique=True)
    position = models.IntegerField(default=0)


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

    def __unicode__(self):
        """ readable representation """
        return u"path %s pos %d" % (self.path or '/', self.position)

WHEEL_NODE_BASECLASS = NodeBase
class Node(WHEEL_NODE_BASECLASS):
    pass
