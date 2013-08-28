from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings

from haystack import indexes

from wheelcms_axle.content import Content
from wheelcms_axle.node import Node
from wheelcms_axle.forms import formfactory, FileFormfactory
from wheelcms_axle.workflows.default import DefaultWorkflow

from wheelcms_axle.models import type_registry
from wheelcms_axle.templates import template_registry

from .impexp import WheelSerializer
from .actions import action

from two.ol.util import classproperty


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
    class WheelIndex(indexes.SearchIndex):
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
                                  model_attr='node__slug')
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

        def index_queryset(self):
            """ Should the content to be indexed restricted here?
                Or index everything and apply filters depending on
                context? """
            ## only index content that's attached.
            return spoke.model.objects.filter(node__isnull=False)
    return WheelIndex

class Spoke(object):
    model = Content  ## is it smart to set this to Content? A nonsensible default..
    workflowclass = DefaultWorkflow

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
        self.o = o
        self.instance = o  ## keep self.o for backward compat

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
        return cls.model._meta.object_name + " content"

    def description(self):
        """ attempt to provide some sort of description """
        return self.instance.description

    def workflow(self):
        """ the workflow, initialized to this spoke """
        return self.workflowclass(self)

    def state(self):
        """ current workflow state information for this spoke """
        return dict(key=self.instance.state, label=self.workflow().state())

    def view_template(self):
        if not self.instance.template or \
           not template_registry.valid_for_model(self.model, self.instance.template):
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

    @classmethod
    def addable_children(cls):
        """ return spokes that can be added as children """
        def addable(t):
            """ check it it's addable, implicitly or explicitly """
            if t.implicit_add:
                return True
            explicit = set(cls.children or ()) | set(cls.explicit_children or ())
            return t in explicit

        if cls.children is None:
            ch = [t for t in type_registry.values() if addable(t)]
        else:
            ch = cls.children

        return ch

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
        return {}

    def can_discuss(self):
        """ determine if content can be discussed. Either by explicit
            database setting or by content default. """
        explicit = self.instance.discussable
        if explicit is None:
            return self.discussable
        return explicit

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
