import inspect

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings

from taggit.models import Tag

from haystack import indexes


from wheelcms_axle.content import Content
from wheelcms_axle.node import Node
from wheelcms_axle.forms import formfactory, FileFormfactory

from wheelcms_axle.registries import core

from wheelcms_axle.models import type_registry
from wheelcms_axle.templates import template_registry
from wheelcms_axle import permissions as p, roles

from .context import ContextWrappable

from .impexp import WheelSerializer
from .actions import action, tab

from .utils import classproperty, json

from warnings import warn

import auth

from drole.models import RolePermission
from drole.types import Role, Permission

class SpokeCharField(indexes.CharField):
    def __init__(self, spoke, *args, **kw):
        super(SpokeCharField, self).__init__(*args, **kw)
        self.spoke = spoke

    def prepare(self, obj):
        instance = self.spoke(obj)
        ma = getattr(instance, self.model_attr, None)
        if ma:
            if callable(ma):
                res = ma()
            else:
                res = ma
        if res is None:
            return super(SpokeCharField, self).prepare(obj)

        return self.convert(res)

def indexfactory(spoke):
    """ return a generic index definition bound to 'spoke' """
    class WheelIndex(indexes.SearchIndex, indexes.Indexable):
        text = SpokeCharField(spoke=spoke, document=True,
                              model_attr='searchable_text')
        title = indexes.CharField(stored=True, indexed=False,
                                  model_attr="title")
        language = indexes.CharField(stored=True, indexed=True,
                                  model_attr="language")
        description = indexes.CharField(stored=True, indexed=False,
                              model_attr='description')
        state = indexes.CharField(stored=True, indexed=True,
                                  model_attr='state')
        meta_type = indexes.CharField(stored=True, indexed=True,
                                      model_attr='meta_type')
        path = indexes.CharField(stored=True, indexed=True,
                              model_attr='get_absolute_url')
        slug = indexes.CharField(stored=True, indexed=True,
                                  model_attr='node__slug', default='')
        created = indexes.DateField(stored=True, indexed=True,
                                    model_attr="created")
        modified = indexes.DateField(stored=True, indexed=True,
                                     model_attr="modified")
        publication = indexes.DateField(stored=True, indexed=True,
                                        model_attr="publication")
        expire = indexes.DateField(stored=True, indexed=True,
                                   model_attr="expire", null=True)
        icon = SpokeCharField(spoke=spoke, stored=True, indexed=False,
                              model_attr="full_icon_path")
        owner = SpokeCharField(spoke=spoke, stored=True, indexed=True,
                               model_attr="owner_name")

        def index_queryset(self, using=None):
            """ Should the content to be indexed restricted here?
                Or index everything and apply filters depending on
                context? """
            ## only index content that's attached.
            return spoke.model.objects.filter(node__isnull=False)

        def get_model(self):
            return spoke.model

    return WheelIndex


class Spoke(ContextWrappable):

    model = Content  ## is it smart to set this to Content? A nonsensible default..
    permissions = dict(
        create=p.create_content,
        edit=p.edit_content,
        view=p.view_content,
        delete=p.delete_content,
        list=p.list_content,
    )

    permission_assignment = {
        p.view_content: (roles.owner, roles.editor, roles.admin),
        p.edit_content: (roles.owner, roles.editor, roles.admin),
        p.create_content: (roles.owner, roles.editor, roles.admin),
        p.delete_content: (roles.owner, roles.editor, roles.admin),
        p.list_content: (roles.owner, roles.editor, roles.admin),
        p.change_auth_content: (roles.owner, roles.admin),
        p.modify_settings: (roles.admin,),
    }

    basetabs = (
        dict(id="attributes", label="Attributes", action="edit",
             permission=p.edit_content),
    )

    ## None means no restrictions, () means no subcontent allowed
    children = None

    ## The primary sub content. Used to create a quick shortcut
    primary = None

    ## can it be implicitly added?
    implicit_add = True

    ## explicit children - explicit children that can be added
    explicit_children = None

    ## is content discussable? Iow, is commenting allowed?
    discussable = False

    serializer = WheelSerializer

    ## default language - None to let the system decide,
    ## or an explicit language (usually 'any') to provide an overriding
    ## default
    default_language = None

    document_fields = ('title', 'description')

    ## index this type of content?
    add_to_index = True

    type_icon = icon = "page.png"

    def __init__(self, o):
        self.instance = o

    def __eq__(self, other):
        """ it may be useful to test equality of spokes in tests """
        return other and self.__class__ is other.__class__ and \
               self.instance == other.instance


    def __ne__(self, other):
        """ it may be useful to test equality of spokes in tests """
        return not self.__eq__(other)

    def tabs(self):
        """ Provide a hook to modify the tabs depending on the spoke
            context """
        decorated_tabs = []

        explicit_tabs = {}

        from .actions import action_registry

        for (name, a) in action_registry.iteritems():
            for (h, epath, espoke) in a:
                # import pdb; pdb.set_trace()
                if getattr(h, 'action', False) and getattr(h, 'tab', False):
                    if h.condition and not h.condition(self):
                        continue

                    if espoke and espoke != self.__class__:
                        continue

                    decorated_tabs.append(dict(id=h.tab_id, label=h.tab_label,
                                              action="+"+name,
                                              permission=h.permission))
                    explicit_tabs[name] = True

        for (name, m) in inspect.getmembers(self, inspect.ismethod):
            ## 
            if name in explicit_tabs:
                continue

            #if name == "test_tab":
            #    import pytest; pytest.set_trace()
            if getattr(m, 'action', False) and getattr(m, 'tab', False):
                if m.condition and not m.condition(self):
                    continue
                id = getattr(m, 'tab_id', name)
                label = getattr(m, 'tab_label', id)
                decorated_tabs.append(dict(id=id, label=label, action="+"+name,
                                           permission=m.permission))
        return self.basetabs + tuple(decorated_tabs)

    def assign_perms(self):
        """ invoked by a signal handler upon creation: Set initial
            permissions """
        auth.assign_perms(self.instance, self.permission_assignment)

    def update_perms(self, perms):
        """ Update specific permissions, e.g. after a workflow change """
        auth.update_perms(self.instance, perms)

    @property
    def o(self):
        warn("{0}.o is obsolete, please use {0}.instance".format(self),
             DeprecationWarning, stacklevel=2)
        return self.instance

    def icon_base(self):
        return settings.STATIC_URL + "img/icons"

    def full_icon_path(self):
        """ return the full icon path. Used for storing the icon in the
            search index """
        return self.icon_base() + '/' + self.icon

    @classmethod
    def full_type_icon_path(cls):
        """
            Icons are instance specific, this allows an spoke to change its
            content depending on the content it holds. E.g. turn a generic
            file icon into a pdf file icon.

            But in certain cases we want a generic type icon without an
            instance, e.g. in the create popup
        """
        return settings.STATIC_URL + "img/icons/" + cls.type_icon

    def owner_name(self):
        """ return the owner's name, as good as possible """
        try:
            owner = self.instance.owner
        except User.DoesNotExist:
            return "Anonymous"

        if owner is None:
            return "Anonymous"

        name = owner.get_full_name()

        return name.strip() or owner.username

    ## Experimental API
    @property
    def node(self):
        """
            Return the node this Spoke is attached to
        """
        return self.instance.node

    @classmethod
    def fromNode(cls, node, slug=None):
        """
            Retrieve a spoke from a node, optionally resolving a childnode
        """
        if slug:
            node = node.child(slug)
            if node is None:
                return None
        content = node.content()
        if content is None:
            return None
        return content.spoke()

    @classmethod
    def create(cls, **kw):
        """
            Create a spoke with its instance, not connected
            to a specific node.
        """
        return cls(cls.model(**kw))

    def save(self, *a, **kw):
        """ save the instance """
        self.instance.save(*a, **kw)
        return self

    @classmethod
    def index(cls):
        """ generate the search index definition """
        return indexfactory(cls)

    @classproperty
    def form(cls):
        return formfactory(cls.model)

    @classproperty
    def light_form(cls):
        """ a smaller, lightweight form with minimal requirements """
        return cls.form

    @classmethod
    def name(cls):
        """ This needs namespacing. But a model determines its name based
            on the classname and doesn't know about namespaces or packages """
        return cls.model.get_name()

    @classproperty
    def title(cls):
        """ The title for this type, not for it's specific content """
        ## XXX somewhat inconsistent with spoke.description
        return cls.model._meta.object_name + " content"

    def description(self):
        """ attempt to provide some sort of description """
        warn("Spoke.description is deprecated, "
             "use context or .instance.description", stacklevel=2)
        return self.instance.description

    def workflow(self):
        """ the workflow, initialized to this spoke """
        return core.workflow[self.__class__](self)


    def state(self):
        """ current workflow state information for this spoke """
        return dict(key=self.instance.state, label=self.workflow().state())

    @classmethod
    def create_template(self, request, parent):
        """ If we're about to create, there's no actual instance of
            the spoke yet, hence the classmethod
            parent may be unattached, so we can't ask for a parent spoke
            instance
        """
        return "wheelcms_axle/create.html"

    def update_template(self):
        return "wheelcms_axle/update.html"

    def view_template(self):
        if not self.instance.template or \
           not template_registry.valid_for_model(self.model,
                                                 self.instance.template):
            default = template_registry.defaults.get(self.model)
            if default:
                return default

            all = template_registry.get(self.model, [])
            if len(all) == 1:
                return all[0][0]

            return "wheelcms_axle/content_view.html"

        return self.instance.template

    def list_template(self):
        ## perform a lookup for a registered LIST template?
        return "wheelcms_axle/contents.html"

    def detail_template(self):
        """ A small detail template, used in browse modal """
        return "wheelcms_axle/popup_detail.html"

    def fields(self):
        """ iterate over fields in model """
        for i in self.instance._meta.fields:
            yield (i.name, getattr(self.instance, i.name))

    def allow_spokes(self, types):
        """ Set which children are allowed as subcontent """
        self.instance.allowed = ",".join(t.name() for t in types)

    def allowed_spokes(self):
        """
            Return the spokes that can be added to the current instance.
            This can be either the spoke's class default, or an instance
            specific config (instance.allowed).

            If the specific config is an empty string, no subcontent is
            allowed.

            If the specific config is a list of comma separated type names,
            those are allowed (even non-implicit ones)

            If the specific config is None, de class default applies.
        """
        def addable(t):
            """ check it it's addable, implicitly or explicitly """
            if t.implicit_add:
                return True
            explicit = set(self.children or ()) | \
                       set(self.explicit_children or ())
            return t in explicit

        if self.instance.allowed == "":
            ch = ()
        elif self.instance.allowed is None:
            # Class default
            if self.children is None:
                ch = [t for t in type_registry.values() if addable(t)]
            else:
                ch = self.children
        else:
            ch = [type_registry.get(p)
                  for p in self.instance.allowed.split(",")]
            ## filter out stale entries. Log?
            ch = filter(None, ch)
        return ch

    def addable_children(self):
        """ deprecated name """
        warn("Spoke.addable_children is obsolete, "
             "please use allowed_spokes in stead",
             DeprecationWarning, stacklevel=2)
        return self.allowed_spokes()

    def searchable_text(self):
        """ collect, if possible, the value of all fields in 'document_fields'
            and return their values combined. This is to be used as the main
            document index value """
        res = u""
        for f in self.document_fields:
            if hasattr(self.instance, f):
                ff = getattr(self.instance, f)
                if callable(ff):
                    res += " " + ff()
                else:
                    res += " " + ff

        res += " ".join(t.name for t in self.instance.tags.all())

        return res

    def path(self):
        try:
            return self.instance.node.path or '/'
        except Node.DoesNotExist:
            return None

    def context(self, handler, request, node):
        """ hook to add additional data to the context """
        return {'spoke':self}

    def can_discuss(self):
        """ determine if content can be discussed. Either by explicit
            database setting or by content default. """
        explicit = self.instance.discussable
        if explicit is None:
            return self.discussable
        return explicit

    @tab(p.change_auth_content, id="auth", label="Roles/Perms")
    def auth(self, handler, request, action):
        ##
        ## If post, handle/reset perm changes

        if request.method == "POST":
            existing = RolePermission.assignments(self.instance)
            assignments = request.POST.getlist('assignment')
            for e in existing:
                if "{0}/{1}".format(e.permission, e.role) not in assignments:
                    e.delete()

            for assignment in assignments:
                perm, role = assignment.split('/', 1)
                RolePermission.assign(self.instance, Role(role),
                                      Permission(perm)).save()

        ctx = {'spoke':self}


        roles = Role.all()
        permissions = []

        ## order roles, permissions (alphabetically?)
        for perm in Permission.all():
            d = dict(perm=perm, roles=[])
            perms_per_role = RolePermission.assignments(
                                        self.instance).filter(
                                        permission=perm.id,
                                        ).values_list('role', flat=True)
            r = []
            for role in roles:
                r.append(dict(role=role, checked=role.id in perms_per_role))

            d['roles'] = r

            permissions.append(d)

        ctx['roles'] = roles
        ctx['permissions'] = permissions
        return handler.template("wheelcms_axle/edit_permissions.html", **ctx)

    @action
    @json
    def tags(self, handler, request, action):
        q = request.GET.get('query', '').lower()
        tags = list(Tag.objects.filter(name__istartswith=q
                    ).values_list("name", flat=True).all())
        return tags

class FileSpoke(Spoke):
    @classproperty
    def form(cls):
        return FileFormfactory(cls.model)

    @classproperty
    def light_form(cls):
        return FileFormfactory(cls.model, light=True)

    @action
    def download(self, handler, request, action):
        """ provide a direct download

            What's the best option: redirect to {{MEDIA_URL}}/<path> or
            serve from the cms? The former is far more efficient (can be handled
            by the application server), the latter allows more restrictions,
            headers, mangling, etc.

            For now, let's choose the inefficient option
        """
        ## test workflow state / permissions! XXX

        filename = self.instance.filename or self.instance.title
        content_type = self.instance.content_type or "application/octet-stream"

        response = HttpResponse(self.instance.storage, content_type=content_type)
        response['Content-Type'] = content_type

        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

