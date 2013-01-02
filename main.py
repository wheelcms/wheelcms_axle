from two.ol.base import RESTLikeHandler
from wheelcms_axle.models import Node, type_registry

class WheelRESTHandler(RESTLikeHandler):
    pass


class MainHandler(WheelRESTHandler):
    model = dict(instance=Node, parent=Node)
    instance = None
    parent = None

    def update_context(self, request):
        super(MainHandler, self).update_context(request)
        self.context['type_registry'] = type_registry

    def formclass(self, data=None, instance=None):
        if not self.instance:
            return None

        type = self.instance.content().meta_type

        if not type:
            return None

        typeinfo = type_registry.get(type)
        parent = self.instance.parent()
        return typeinfo.form(parent=parent, data=data, instance=instance)

    @classmethod
    def coerce(cls, i):
        """
            coerce either a parent and instance, a parent or an instance.
            If there's both a parent and an instance, the instance is relative
            to the parent, so resolving needs to be done by combing them

            We're supporting the parent/instance combo (somewhat) but don't
            really need it - <instance>/update works fine, and no instance is
            required for /create
        """
        d = dict()

        parent_path = ""
        if i.get('parent') is not None:
            parent_path = i['parent']
            if parent_path:
                parent_path = '/' + parent_path
            parent = d['parent'] = Node.get(parent_path)
            if parent is None:
                return cls.notfound()

        if i.get('instance') is not None:
            d['instance'] = instance = Node.get(parent_path + '/' + i['instance'])

            if instance is None:
                return cls.notfound()
        return d

    def create(self, *a, **b):
        type = self.request.REQUEST.get('type')
        formclass = type_registry.get(type).form
        attach = self.request.REQUEST.get('attach', False)

        parent = self.parent

        ## if attach: do not accept slug
        if self.post:
            self.form = formclass(data=self.request.POST, parent=parent, attach=attach)
            if self.form.is_valid():
                ## form validation should handle slug uniqueness (?)
                p = self.form.save()
                if attach:
                    parent.set(p)
                else:
                    slug = self.form.cleaned_data['slug']
                    sub = parent.add(slug)
                    sub.set(p)
                return self.redirect(parent.path or '/', success="Ok")
        else:
            self.context['form'] = formclass(attach=attach)
        ## Get spoke model
        self.context['type'] = type = self.request.REQUEST['type']

        typeinfo = type_registry.get(type)
        self.context['typeinfo'] = dict(name=typeinfo.name, title=typeinfo.title)

        self.context['attach'] = attach
        self.context['instance'] = self.parent or '/'
        return self.template("wheelcms_axle/create.html")

    def update(self):
        instance = self.instance
        parent = instance.parent()

        type = instance.content().meta_type
        typeinfo = type_registry.get(type)
        formclass =  typeinfo.form
        slug = instance.slug()

        if self.post:
            self.context['form'] = form = formclass(parent=parent,
                                                    data=self.request.POST,
                                                    instance=instance.content())

            if form.is_valid():
                form.save()
                ## handle changed slug
                slug = form.cleaned_data['slug']
                if slug != self.instance.slug():
                    self.instance.set_slug(slug)

                return self.redirect(instance.path, success="Updated")
        else:
            self.context['form'] = formclass(parent=parent,
                             initial=dict(slug=slug), instance=instance.content())

        return self.template("wheelcms_axle/update.html")

    def view(self):
        """ frontpage / view """
        self.context['instance'] = self.instance
        model = self.instance.content()
        if model:
            self.context['spoke'] = type_registry.get(model.meta_type)(model)
        return self.template("wheelcms_axle/main.html")

    def list(self):
        self.instance = Node.root()
        return self.view()
