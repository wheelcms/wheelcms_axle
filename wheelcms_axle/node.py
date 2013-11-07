import re

from django.utils import translation
from django.db import models, IntegrityError
from django.core.urlresolvers import reverse
from django.conf import settings

from wheelcms_axle.utils import get_active_language
from wheelcms_axle import translate

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
    return get_active_language()


def node_proxy_factory(base, l):
    """
        Create a proxy model based on the base (usually Node or some derivative)
        and language 'l', with 'l' bound as preferred language to that proxy.
        We need to use type() here in stead of defining a class locally because it
        will need to be uniquely named (per language). A generick "LanguageProxy"
        would be cached by django and simply not work.
    """

    class Meta:
        proxy = True

    def __eq__(self, other):
        return isinstance(other, NodeBase) and \
               self.pk == other.pk and \
               self.preferred_language == other.preferred_language

    def __unicode__(self):
        """ readable representation """
        return u"path %s pos %d %s" % (self.tree_path or '/', self.position,
                                       self.preferred_language)

    attrs = dict(Meta=Meta,
                 __module__=base.__module__,
                 __eq__=__eq__,
                 __unicode__=__unicode__,
                   preferred_language=l)

    lang = l.upper() if l else ""
    LanguageProxy = type(str("Node" + lang),
                         (base,),
                         attrs)

    return LanguageProxy


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

    preferred_language = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kw):
        self._slug = kw.get('slug', None)
        self._parent = kw.get('parent', None)
        self._langslugs = kw.get('langslugs', {})
        self.preferred_language = self.preferred_language or None

        try:
            del kw['slug']
        except KeyError:
            pass
        try:
            del kw['parent']
        except KeyError:
            pass
        try:
            del kw['langslugs']
        except KeyError:
            pass

        super(NodeBase, self).__init__(*args, **kw)

    def content(self, language=None, fallback=True):
        from .content import Content
        language = language or self.preferred_language or get_language()

        if fallback:
            langs = translate.fallback_languages(language)
        else:
            langs = [language]

        for l in langs:
            try:
                return self.contentbase.get(language=l).content()
            except Content.DoesNotExist:
                pass
        return None

    def primary_content(self):
        """ what determines which language is primary? First one
            created? A specific language? """
        try:
            return self.contentbase.all()[0].content()
        except IndexError:
            return None

    @property
    def path(self):
        ## self.preferred_language? XXX
        return self.get_path()

    @classmethod
    def get(cls, path, language=None):
        """ retrieve node directly by path. Returns None if not found """
        detect_or_prefer_language = language or get_language()
        try:
            n = Paths.objects.get(path=path, language=detect_or_prefer_language).node
            n.preferred_language = language
            return n
        except Paths.DoesNotExist:
            ## the root may not yet have been created
            if path == "":
                return cls.root(language=detect_or_prefer_language)
            return None


    def set(self, content, replace=False, language=None):
        """
            Set content on the node, optionally replacing existing
            content. This is a more friendly way of setting the node
            on a Content directly
        """
        ## just to be sure, in case it's of type Content in stead of
        ## subclass
        from .content import Content
        content = content.content()
        ## can be taken from content? XXX
        language = language or content.language # language or get_language()

        old = None
        try:
            if self.contentbase.get(language=language):
                if replace:
                    old = self.content()
                    old.node = None
                    old.save()
                else:
                    raise NodeInUse()
        except Content.DoesNotExist:
            pass

        self.contentbase.add(content) #.content_ptr  # XXX is _ptr documented?
        #content.node = self
        ## avoid updating last_modified
        content.save(update_lm=False)
        self.save()

        return old

    @classmethod
    def root(cls, language=None):
        try:
            root = cls.objects.get(tree_path=cls.ROOT_PATH)
        except Node.DoesNotExist:
            root = Node(parent=None, slug="")
            root.save()
        root.preferred_language = language
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
        language = language or self.preferred_language or get_language()
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
            for language, langname in translate.languages():
                try:
                    langpath = Paths.objects.get(node=self, language=language)
                except Paths.DoesNotExist:
                    langpath = Paths(node=self, language=language)

                langslug = translate.language_slug(self._langslugs, self._slug, language)

                if not self._parent:
                    path = '' # '/' + str(self.id) -- be consistent with 'old' behavior, for now
                    langpath.path = langslug
                else:
                    path = self._parent.tree_path + '/' + str(self.id)
                    langpath.path = self._parent.get_path(language) + '/' + langslug
                langpath.save()

            self.tree_path = path
            super(NodeBase, self).save()

    def add(self, path=None, langslugs={}, position=-1, after=None, before=None):
        """ handle invalid paths (invalid characters, empty, too long) """
        ## lowercasing is the only normalization we do
        ## path is actually slug

        slugs = [s.lower() for s in langslugs.values()]
        if path is not None:
            path = path.lower()
            slugs.append(path)

        ## no path specified?
        for slug in slugs:
            if not self.validpathre.match(slug):
                raise InvalidPathException(slug)
        if not slugs:
            raise InvalidPathException("No slug or map specified")

        position = self.find_position(position, after, before)

        child = self.__class__(parent=self, slug=path, langslugs=langslugs,
                               position=position)
        try:
            child.save()
        except IntegrityError:
            raise DuplicatePathException(slugs)
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

        if copy:
            slug_per_lang = {}
            for p in node.paths.all():
                lang, path = p.language, p.path

                if path == "":
                    slug = "root"
                else:
                    base_slug = slug = path.rsplit('/', 1)[1]

                count = 0
                while self.child(slug, lang):
                    slug = "copy_%s_of_%s" % (count, base_slug)
                slug_per_lang[lang] = slug


            base = self.add(langslugs=slug_per_lang)
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
                    langslugs = dict((p.language, p.path.rsplit("/", 1)[1]) for  p in o.paths.all())
                    n = Node(langslugs=langslugs, parent=base)
                    n.save()
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

            ## XXX somehow batch/transaction this
            for o in node_proxy_factory(Node, self.preferred_language).objects.offspring(node):
                o.tree_path = self.tree_path + o.tree_path[len(oldbase):]
                o.save()
                success.append(o.tree_path)
            node.tree_path = self.tree_path + '/' + str(node.id)
            ## move to end
            node.position = self.find_position(position=-1)
            node.save()
            success.append(node.tree_path)

            ## the great renaming
            # import pytest; pytest.set_trace()
            for language, langname in translate.languages():
                try:
                    localized_path = Paths.objects.get(node=node, language=language)
                except Paths.DoesNotExist:
                    continue

                slug = localized_path.path.rsplit('/', 1)[1]

                mypath = self.get_path(language)
                newpath = mypath + '/' + slug
                count = 0

                while Paths.objects.filter(path=newpath, language=language).exists():
                    newpath = mypath + '/' +  slug + "_" + str(count)
                    count += 1

                #if testmode:
                #if Paths.objects.filter(path=newpath, language=language).exists():
                #    raise DuplicatePathException(newpath, language)
                #else:
                for p in Paths.objects.filter(Q(path=localized_path.path) |
                                              Q(path__startswith=localized_path.path + '/'),
                                              language=language):
                    remainder = p.path[len(localized_path.path):]

                    p.path = newpath + remainder

                    p.save()


        return node, success, failed

    def remove(self, childslug, language=None):
        """ remove a child, recursively """
        child = self.child(childslug, language)

        if child is None:
            raise NodeNotFound(self.tree_path + '/' + childslug)
        node_proxy_factory(Node, self.preferred_language).objects.offspring(child).delete()
        child.delete()

    def parent(self):
        """ return the parent for this node """
        if self.isroot():
            return self
        parentpath, mypath = self.tree_path.rsplit("/", 1)
        parent = node_proxy_factory(self.__class__, self.preferred_language).objects.get(tree_path=parentpath)
        return parent

    def childrenq(self, order="position", **kw):
        """ return the raw query for children """

        return node_proxy_factory(self.__class__, self.preferred_language).objects.children(self).order_by(order).filter(**kw)

    def children(self, order="position"):
        return self.childrenq(order=order)

    def child(self, slug, language=None):
        """ return a specific child by its slug """
        childpath = self.get_path(language) + '/' + slug

        return self.get(childpath, language)

    def slug(self, language=None):
        """ last part of self.path """
        return self.get_path(language).rsplit("/", 1)[-1]

    def rename(self, slug, language=None):
        """ change the slug """
        if self.isroot():
            raise CantRenameRoot()

        ## if no language was specified, rename all
        languages = [language] if language else [l[0] for l in translate.languages()]

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
        language = language or self.preferred_language

        active_language = translation.get_language()
        try:
            if language:
                translation.activate(language)
            return reverse('wheel_main', kwargs={'instance':self.get_path(language).lstrip('/')})
        finally:
            if language:
                translation.activate(active_language)

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
    path = models.CharField(blank=False, max_length=255) ## length constraint for mysql
    node = models.ForeignKey(Node, related_name="paths")

    def __unicode__(self):
        return u"path [%s] for language %s on node %s" % (self.path, self.language, self.node)
