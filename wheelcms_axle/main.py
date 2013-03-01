from two.ol.base import RESTLikeHandler, applyrequest, context, json
from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry, Content, ImageContent

from wheelcms_axle.spoke import FileSpoke

from wheelcms_axle.toolbar import Toolbar
from wheelcms_axle import queries

from wheelcms_axle.base import WheelHandlerMixin

from .templates import template_registry


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

        typename = self.instance.content().get_name()

        typeinfo = type_registry.get(typename)
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
        # import pdb; pdb.set_trace()
        
        if not self.hasaccess():
            return self.forbidden()

        formclass = type_registry.get(type).form

        parent = self.parent
        if parent and parent.path:
            parentpath = parent.path
        else:
            parentpath = '/'

        self.context['redirect_cancel'] = parentpath + "?info=Create+cancelled"
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
            self.context['form'] = formclass(parent=parent, attach=attach)
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

        self.context['redirect_cancel'] = (self.instance.path or '/') + \
                                          "?info=Update+cancelled"
        self.context['toolbar'] = Toolbar(self.instance, status="edit")

        typename = instance.content().get_name()
        typeinfo = type_registry.get(typename)
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
        action = self.kw.get('action', '')
        spoke = self.spoke()

        if spoke and not spoke.workflow().is_published():
            if not self.hasaccess():
                return self.forbidden()

        if action:
            handler = getattr(spoke, action, None)
            if handler and getattr(handler, 'action', False):
                return handler(self, self.request, action)
            else:
                return self.notfound()

        self.context['toolbar'] = Toolbar(self.instance)
        ## experimental
        if spoke:
            tpl = spoke.view_template()
            ctx = template_registry.context.get((spoke.__class__, tpl))
            if ctx:
                self.context.update(ctx(self.instance))

        if spoke:
            return self.template(spoke.view_template())
        return self.template("wheelcms_axle/nospoke.html")

    def list(self):
        self.instance = Node.root()
        return self.view()

    def handle_list(self):
        if not self.hasaccess():
            return self.forbidden()
        self.context['toolbar'] = Toolbar(self.instance, status="list")
        self.context['breadcrumb'] = self.breadcrumb(operation="Contents")
        return self.template("wheelcms_axle/contents.html")

    def handle_contents(self):
        """ handle the /contents method. Usually this will give a listing
            of child-content, but in certain cases this makes no sense (e.g.
            childless content, or content that simply can't have children.

            This also may behave differently depending on the user's access
        """
        if self.spoke() and self.spoke().addable_children():
            return self.redirect(self.instance.path + '/list')
        return self.redirect(self.instance.path)

    def handle_popup(self):
        """ popup experiments - #524 """
        return self.template("wheelcms_axle/popup.html")

    @json
    @applyrequest
    def handle_panel(self, path, mode):
        return self.panels(path, mode)

    def panels(self, path, mode):
        """
            Generate panels for the file selection popup
            mode can be either "link" (any content) or "image" (only image
            based content)
        """
        if not self.hasaccess():
            return self.forbidden()

        ## remove optional 'action', marked by a +
        ## not sure if this is the right place to do this, or if the browser
        ## modal should have been invoked without the action in the first place
        if '+' in path:
            path = path.split("+", 1)[0].rstrip('/')

        node = Node.get(path)
        panels = []

        for i in range(3):
            content = node.content()

            if content:
                ## FileSpoke also includes ImageSpoke
                # import pdb; pdb.set_trace()

                spoke = content.spoke()
                addables = [x for x in spoke.addable_children()
                            if issubclass(x, FileSpoke)]
                instance = dict(children=[], path=node.path or '/',
                                title=content.title,
                                meta_type=content.meta_type,
                                content=content,
                                spoke=spoke,
                                addables=addables)
            else:
                addables = [x for x in type_registry.values()
                            if issubclass(x, FileSpoke)]
                instance = dict(children=[], path=node.path or '/',
                                title="Unattached node",
                                meta_type="none",
                                content=None,
                                spoke=None,
                                addables=addables)

            for child in node.children():
                selectable = False

                if mode == "link":
                    selectable = True
                elif isinstance(child.content(), ImageContent):
                    selectable = True

                selected = path == child.path or \
                           path.startswith(child.path + '/')
                instance['children'].append(
                                      dict(title=child.content().title,
                                           path=child.path,
                                           selectable=selectable,
                                           meta_type=child.content().meta_type,
                                           selected=selected))

            panels.insert(0,
                          self.render_template("wheelcms_axle/popup_list.html",
                                               instance=instance,
                                               path=path,
                                               mode=mode,
                                               selectable=(i==0)))
            if node.isroot():
                break
            node = node.parent()
        crumbs = []
        node = Node.get(path)
        while True:
            if node.isroot():
                crumbs.insert(0, dict(path=node.path, title="Home"))
                break
            crumbs.insert(0, dict(path=node.path or '/', title=node.content().title))
            node = node.parent()

        crumbtpl = self.render_template("wheelcms_axle/popup_crumbs.html", crumbs=crumbs)
        return dict(panels=panels, path=path or '/', crumbs=crumbtpl)

    @json
    @applyrequest
    def handle_fileup(self, type):
        # import pdb; pdb.set_trace()

        if not self.hasaccess():
            return self.forbidden()

        formclass = type_registry.get(type).light_form

        parent = self.instance

        ## use get() to return type-specific rendered light-form?

        if not self.post:
            return dict(form=self.render_template("wheelcms_axle/popup_upload.html",
                                                  form=formclass(parent=parent),
                                                  type=type))


        self.context['form'] = \
        self.form = formclass(data=self.request.POST,
                              parent=parent,
                              attach=False,
                              files=self.request.FILES,
                              )

        if self.form.is_valid():
            ## form validation should handle slug uniqueness (?)
            p = self.form.save(commit=False)
            if self.user().is_authenticated():
                p.owner = self.user()
            p.save()
            slug = self.form.cleaned_data['slug']
            sub = parent.add(slug)
            sub.set(p)
            return dict(status="ok", path=sub.path)

        ## for now, assume that if something went wrong, it's with the uploaded file
        return dict(status="error", errors=dict(storage=self.form.errors['storage'].pop()))


    def handle_download(self):
        """
            This doesn't work as expected. handle_download is defined on the spoke,
            it requires support in the handler in order to be accessed.

            XXX

            We need a generic way to expose additional methods on spokes
        """
        try:
            return self.spoke().handle_download()
        except AttributeError:
            return self.notfound()
