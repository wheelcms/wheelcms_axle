import re

from django.utils import translation
from django.db import models, IntegrityError
from django.core.urlresolvers import reverse
from django.conf import settings



class NodeException(Exception):
    """ Base class for all Node exceptions """

class DuplicatePathException(NodeException):
    """ the path is already in use """

class InvalidPathException(NodeException):
    """ The path contains non-valid chars or is too short """

class NodeInUse(NodeException):
    """ the node already has content attached to it """

class CantMoveToOffspring(NodeException):
    """ a node cannot be moved to one of its offspring nodes """

class CantRenameRoot(NodeException):
    """ the root's path is "" which cannot be changed """

class NodeNotFound(NodeException):
    """ raised if a node is not found """

from django.db.models.query import QuerySet
from django.utils import timezone
from django.db.models import Q
import random

def random_path():
    return hex(random.randrange(0, 10**20))

def get_language():
    language = translation.get_language()
    if language not in getattr(settings, 'CONTENT_LANGUAGES', ()) and getattr(settings, 'FALLBACK', None):
        language = settings.FALLBACK
    return language

class NodeQuerySet(QuerySet):
    def children(self, node):
        """ only return direct children """
        return self.filter(
                  tree_path__regex="^%s/[%s]+$" % (node.tree_path, Node.ALLOWED_CHARS),
                  )

    def offspring(self, node):
        """ children, grandchildren, etc """
        return self.filter(
                  tree_path__regex="^%s/[%s]+" % (node.tree_path, Node.ALLOWED_CHARS),
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

    tree_path = models.CharField(max_length=255, blank=False, unique=True, default=random_path)
    position = models.IntegerField(default=0)

    objects = NodeManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kw):
        self._slug = kw.get('slug', None)
        self._parent = kw.get('parent', None)
        try:
            del kw['slug']
        except KeyError:
            pass
        try:
            del kw['parent']
        except KeyError:
            pass

        super(NodeBase, self).__init__(*args, **kw)

    def content(self):
        from .content import Content
        try:
            return self.contentbase.content()
        except Content.DoesNotExist:
            return None

    @property
    def path(self):
        return self.get_path()

    @classmethod
    def get(cls, path, language=None):
        """ retrieve node directly by path. Returns None if not found """
        language = language or get_language()
        try:
            return Paths.objects.get(path=path, language=language).node
        except Paths.DoesNotExist:
            ## the root may not yet have been created
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
        try:
            return cls.objects.get(tree_path=cls.ROOT_PATH)
        except Node.DoesNotExist:
            root = Node(parent=None, slug="")
            root.save()
            return root


    def isroot(self):
        return self.tree_path == self.ROOT_PATH

    def is_ancestor(self, node):
        return node.tree_path.startswith(self.tree_path + '/')

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

    def get_path(self, language=None):
        language = language or get_language()
        return Paths.objects.get(node=self, language=language).path

    def save(self, *args, **kw):
        ## If the object has not yet been saved (ever), create the node's paths
        saved = True
        if self.pk is None:
            saved = False


        ## first save the object so we can create references
        super(NodeBase, self).save(*args, **kw)

        ## create paths based on self._slug / self._parent which were passed to __init__
        if not saved:
            for language in settings.CONTENT_LANGUAGES:
                try:
                    langpath = Paths.objects.get(node=self, language=language)
                except Paths.DoesNotExist:
                    langpath = Paths(node=self, language=language)

                if not self._parent:
                    path = '' # '/' + str(self.id) -- be consistent with 'old' behavior, for now
                    langpath.path = self._slug
                else:
                    path = self._parent.tree_path + '/' + str(self.id)
                    langpath.path = self._parent.get_path(language) + '/' + self._slug
                langpath.save()

            self.tree_path = path
            super(NodeBase, self).save()

    def add(self, path, position=-1, after=None, before=None):
        """ handle invalid paths (invalid characters, empty, too long) """
        ## lowercasing is the only normalization we do
        path = path.lower()

        if not self.validpathre.match(path):
            raise InvalidPathException(path)

        position = self.find_position(position, after, before)

        #if path == "child":
        #    import pytest; pytest.set_trace()

        child = self.__class__(parent=self, slug=path,
                               position=position)
        try:
            child.save()
        except IntegrityError:
            raise DuplicatePathException(path)
        return child

    def move(self, child, position=-1, after=None, before=None):
        """ move (reorder) an existing child. This does not take into account
            that the child already has a position in the child-order, but that
            shouldn't make a significant difference

            This method does not move nodes to *different* nodes (e.g. paste)
       """

        position = self.find_position(position, after, before)
        child.position = position
        child.save()

    def paste(self, node, copy=False):
        """
            Move a node elsewhere in the tree, optionally copying the node
            (copy-paste) or deleting the original (cut-paste)
        """
        ## a move is just rewriting/renaming the child and its offspring,
        ## a copy is recreating the node

        ## ancestor nodes cannot be moved into offspring nodes, they can be
        ## copied, but avoid recursion.

        ## how to deal with the position? Insert at the bottom?

        from .content import ContentCopyException

        failed = []
        success = []

        def unique_slug(slug):
            orig_slug = slug
            count = 0
            while self.child(slug) is not None:
                slug = "%s_%d" % (orig_slug, count)
                count += 1
            return slug

        if copy:
            origpath = node.tree_path
            if origpath != '':
                origbase, slug = origpath.rsplit("/", 1)
            else:
                origbase, slug = "", "root"

            slug = unique_slug(slug)
            base = self.add(slug)
            if node.content():
                try:
                    node.content().copy(node=base)
                    success.append(node.tree_path)
                except ContentCopyException:
                    failed.append((node.tree_path, "Content cannot be copied"))
                    base.delete()
                    ## no need to continue
                    return base, success, failed

            for o in Node.objects.offspring(node).order_by("tree_path"):
                ## skip all offspring of a failed node
                for f, reason in failed:
                    if o.tree_path.startswith(f + '/'):
                        break
                else:
                    path = self.tree_path + '/' + slug + o.tree_path[len(origpath):]
                    n, _ = Node.objects.get_or_create(tree_path=path)
                    if o.content():
                        try:
                            o.content().copy(node=n)
                            success.append(o.tree_path)
                        except ContentCopyException:
                            n.delete()
                            failed.append((o.tree_path, "Content cannot be copied"))
            return base, success, failed

        else:
            if node == self or node.is_ancestor(self):
                raise CantMoveToOffspring()
            oldpath = node.tree_path
            oldbase, slug = oldpath.rsplit("/", 1)
            if oldbase == self.tree_path:
                ## pasting into its own parent, nothing to do
                return node, success, failed

            slug = unique_slug(slug)

            ## XXX somehow batch/transaction this
            for o in Node.objects.offspring(node):
                o.tree_path = self.tree_path + '/' + slug + o.tree_path[len(oldpath):]
                o.save()
                success.append(o.tree_path)
            node.tree_path = self.tree_path + '/' + slug
            ## move to end
            node.position = self.find_position(position=-1)
            node.save()
            success.append(node.tree_path)

        return node, success, failed

    def remove(self, childslug):
        """ remove a child, recursively """
        child = self.child(childslug)
        if child is None:
            raise NodeNotFound(self.tree_path + '/' + childslug)
        child.delete()
        recursive = Node.objects.filter(tree_path__startswith=self.tree_path + '/' +
                                                         childslug + '/')
        recursive.delete()

    def parent(self):
        """ return the parent for this node """
        if self.isroot():
            return self
        parentpath, mypath = self.tree_path.rsplit("/", 1)
        parent = self.__class__.objects.get(tree_path=parentpath)
        return parent

    def childrenq(self, order="position", **kw):
        """ return the raw query for children """
        return self.__class__.objects.children(self).order_by(order).filter(**kw)

    def children(self, order="position"):
        return self.childrenq(order=order)

    def child(self, slug, language=None):
        """ return a specific child by its slug """
        childpath = self.get_path(language) + '/' + slug

        return self.get(childpath)

    def slug(self, language=None):
        """ last part of self.path """
        return self.get_path(language).rsplit("/", 1)[-1]

    def rename(self, slug, language=None):
        """ change the slug """
        if self.isroot():
            raise CantRenameRoot()

        ## if no language was specified, rename all
        languages = [language] if language else settings.CONTENT_LANGUAGES

        for testmode in (True, False):
            ## first loop checks if all relevant languages can be renamed, second loop renames
            for language in languages:
                try:
                    localized_path = Paths.objects.get(node=self, language=language)
                except Paths.DoesNotExist:
                    continue

                newpath = localized_path.path.rsplit("/", 1)[0] + "/" + slug

                if testmode:
                    if Paths.objects.filter(path=newpath, language=language).exists():
                        raise DuplicatePathException(newpath, language)
                else:
                    for p in Paths.objects.filter(Q(path=localized_path.path) |
                                                  Q(path__startswith=localized_path.path + '/'),
                                                  language=language):
                        remainder = p.path[len(localized_path.path):]
                        p.path = newpath + remainder
                        p.save()


    def get_absolute_url(self, language=None):
        ## strip any leading / since django will add that as well
        return reverse('wheel_main', kwargs={'instance':self.get_path(language).lstrip('/')})

    def __unicode__(self):
        """ readable representation """
        return u"path %s pos %d" % (self.tree_path or '/', self.position)

WHEEL_NODE_BASECLASS = NodeBase
class Node(WHEEL_NODE_BASECLASS):
    pass

class Paths(models.Model):
    class Meta:
        unique_together = (("language", "path"), )

    language = models.CharField(max_length=10, blank=False)
    path = models.CharField(max_length=255, blank=False)
    node = models.ForeignKey(Node, related_name="paths")

    def __unicode__(self):
        return u"path [%s] for language %s on node %s" % (self.path, self.language, self.node)
