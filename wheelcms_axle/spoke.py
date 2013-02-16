
from django.http import HttpResponse
from wheelcms_axle.content import Content
from wheelcms_axle.forms import formfactory, FileFormfactory
from wheelcms_axle.workflows.default import DefaultWorkflow

from wheelcms_axle.models import type_registry
from wheelcms_axle.templates import template_registry

from .impexp import WheelSerializer

from two.ol.util import classproperty


class Spoke(object):
    model = Content  ## is it smart to set this to Content? A nonsensible default..
    workflowclass = DefaultWorkflow

    ## None means no restrictions, () means no subcontent allowed
    children = None

    ## can it be implicitly added?
    implicit_add = True

    ## explicit children - explicit children that can be added
    explicit_children = None

    serializer = WheelSerializer

    def __init__(self, o):
        self.o = o
        self.instance = o  ## keep self.o for backward compat

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
        return cls.model.get_name()  ## app_label

    @classmethod
    def title(cls):
        """ a default title """
        return cls.model._meta.object_name + " content"

    def workflow(self):
        return self.workflowclass(self)

    def view_template(self):
        if not self.o.template or \
           not template_registry.valid_for_model(self.model, self.o.template):
            default = template_registry.defaults.get(self.model)
            if default:
                return default

            all = template_registry.get(self.model, [])
            if len(all) == 1:
                return all[0][0]

            return "wheelcms_axle/content_view.html"

        return self.o.template

    def detail_template(self):
        """ A small detail template, used in browse modal """
        return "wheelcms_axle/popup_detail.html"

    def fields(self):
        """ iterate over fields in model """
        for i in self.o._meta.fields:
            yield (i.name, getattr(self.o, i.name))

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


class FileSpoke(Spoke):
    @classproperty
    def form(cls):
        return FileFormfactory(cls.model)

    @classproperty
    def light_form(cls):
        return FileFormfactory(cls.model, light=True)

    def action_download(self, handler, request, action):
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
