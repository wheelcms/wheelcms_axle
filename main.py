from two.ol.base import RESTLikeHandler, applyrequest, context
from wheelcms_axle.models import Node, type_registry, Content
from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle import queries

from wheelcms_axle.base import WheelHandlerMixin

class WheelRESTHandler(RESTLikeHandler, WheelHandlerMixin):
    pass


class MainHandler(WheelRESTHandler):
    model = dict(instance=Node, parent=Node)
    instance = None
    parent = None

    def update_context(self, request):
        super(MainHandler, self).update_context(request)

    @context
    def toplevel(self):
        """ return toplevel navigatable/visible items. Perhaps, when logged in,
            show unpublished/not in navigation?

            Return Node or Spokes?
        """
        context = self.parent
        if self.instance:
            context = self.instance

        for child in queries.toplevel_visible_children():
            ## make sure /foo/bar does not match in /football by adding the /
            if child == context or context.path.startswith(child.path + '/'):
                yield dict(active=True, node=child)
            else:
                yield dict(active=False, node=child)


    @context
    def spoke(self):
        """ return type info for the current content, if any """
        model = self.instance.content()
        if model:
            return model.spoke()
        return None

    @context
    def content(self):
        """ return the actual content for the node / spoke """
        modelinstance = self.instance.content()
        if modelinstance:
            return modelinstance
        return None

    def formclass(self, data=None, instance=None):
        """
            Find and initialize the appropriate form for the current
            instance. Not consistently used XXX
        """
        if not self.instance or not self.instance.content():
            ## there's no instance, or it's not attached to content
            return None

        type = self.instance.content().meta_type

        if not type:
            return None

        typeinfo = type_registry.get(type)
        parent = self.instance.parent()
        try:
            content = instance.content()
        except Content.DoesNotExist:
            content = None
        return typeinfo.form(parent=parent, data=data, instance=content)

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
            instance_path = i['instance']
            if not instance_path:  ## it can be ""
                path = parent_path
            else:
                path = parent_path + "/" + instance_path

            d['instance'] = instance = Node.get(path)

            if instance is None:
                return cls.notfound()
        return d

    def hasaccess(self):
        user = self.user()
        return user.is_active and (user.is_superuser or
                                   user.groups.filter(name="managers").exists())

    @applyrequest
    def create(self, type, attach=False, *a, **b):
        """
            Create new sub-content on a node or attach content to an
            existing node.
        """
        if not self.hasaccess():
            return self.forbidden()

        formclass = type_registry.get(type).form

        parent = self.parent

        ## if attach: do not accept slug
        if self.post:
            self.context['form'] = \
            self.form = formclass(data=self.request.POST,
                                  parent=parent,
                                  attach=attach,
                                  files=self.request.FILES)
            if self.form.is_valid():
                ## form validation should handle slug uniqueness (?)
                p = self.form.save(commit=False)
                if self.user().is_authenticated():
                    p.owner = self.user()
                p.save()
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
        self.context['type'] = type

        typeinfo = type_registry.get(type)
        self.context['typeinfo'] = dict(name=typeinfo.name, title=typeinfo.title)

        self.context['attach'] = attach
        self.context['instance'] = self.parent or '/'
        self.context['breadcrumb'] = self.breadcrumb(operation="Create")
        self.context['toolbar'] = Toolbar(self.instance, status="create")
        return self.template("wheelcms_axle/create.html")

    def update(self):
        if not self.hasaccess():
            return self.forbidden()

        instance = self.instance
        parent = instance.parent()

        self.context['toolbar'] = Toolbar(self.instance, status="edit")

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
                slug = form.cleaned_data.get('slug', None)
                if slug and slug != self.instance.slug():
                    self.instance.rename(slug)

                return self.redirect(instance.path, success="Updated")
        else:
            self.context['form'] = formclass(parent=parent,
                             initial=dict(slug=slug), instance=instance.content())

        self.context['toolbar'].status = 'update'
        self.context['breadcrumb'] = self.breadcrumb(operation="Edit")
        return self.template("wheelcms_axle/update.html")


    @context
    def breadcrumb(self, operation=""):
        """ generate breadcrumb path. """
        base = self.instance or self.parent
        if not base:
            ## parent
            return []

        parts = base.path.split("/")
        res = []
        for i in range(len(parts)):
            subpath = "/".join(parts[:i+1])
            node = Node.get(subpath)
            content = node.content()
            ## last entry should not get path

            path = subpath or '/'
            if not operation:
                if i == len(parts) - 1:
                    path = ""

            if node.isroot():
                if content:
                    title = "Home"
                else:
                    title = "Unattached rootnode"
            else:
                title = content.title if content \
                                      else "Unattached node %s" % (subpath or '/')
            res.append((title, path))

        if operation:
            res.append((operation, ""))

        return res

    def view(self):
        """ frontpage / view """
        if self.spoke() and not self.spoke().workflow().is_published():
            if not self.hasaccess():
                return self.forbidden()

        self.context['toolbar'] = Toolbar(self.instance)
        return self.template("wheelcms_axle/main.html")

    def list(self):
        self.instance = Node.root()
        return self.view()

    def handle_list(self):
        self.context['toolbar'] = Toolbar(self.instance, status="list")
        self.context['breadcrumb'] = self.breadcrumb(operation="Contents")
        return self.template("wheelcms_axle/contents.html")
