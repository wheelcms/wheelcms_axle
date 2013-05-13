from django import forms

from two.ol.base import RESTLikeHandler, applyrequest, context, json, handler
from wheelcms_axle.node import Node, NodeNotFound
from wheelcms_axle.content import type_registry, Content, ImageContent

from wheelcms_axle.spoke import FileSpoke

from wheelcms_axle.toolbar import Toolbar

from wheelcms_axle.base import WheelHandlerMixin

from .templates import template_registry
from .actions import action_registry

import stracks

class WheelRESTHandler(RESTLikeHandler, WheelHandlerMixin):
    pass


def strip_action(s):
    if '+' in s:
        s = s.split("+", 1)[0].rstrip('/')
    return s

class MainHandler(WheelRESTHandler):
    model = dict(instance=Node, parent=Node)
    instance = None
    parent = None

    def update_context(self, request):
        super(MainHandler, self).update_context(request)

    @context
    def body_class(self):
        if self.instance:
            model = self.instance.content()

            if model:
                typename = model.get_name()
                parts = typename.split(".")
                return " ".join("_".join(parts[:i+1]) for i in range(len(parts)))

        return ""

    @context
    def page_title(self):
        """ return the content title, if any """
        if self.instance:
            content = self.instance.content()
            if content:
                return content.title
        return "Unattached node"

    @context
    def spoke(self):
        """ return type info for the current content, if any """
        model = self.instance.content()
        if model:
            return model.spoke()
        return None

    @context
    def typeahead_tags(self):
        """ make this a +action? XXX """
        import json
        from taggit.models import Tag

        tags = list(Tag.objects.values_list("name", flat=True).all())
        return json.dumps(tags)

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

    @classmethod
    def reserved(cls):
        return set(["create", "update", "list"] + \
               [x[7:] for x in dir(cls) if x.startswith("handle_")] + \
               [x for x in dir(cls) if getattr(getattr(cls, x), "ishandler", False)])

    @handler
    @applyrequest
    def create(self, type=None, attach=False, *a, **b):
        """
            Create new sub-content on a node or attach content to an
            existing node.

            WheelCMS's structure doesn't map to two.ol's REST-like Resource
            structure. In two.ol's setup, you have a resource name and
            an optional id, e.g. /person/123

            GETting /person/create would give the create form and POSTing
            to /person would create a new person. POSTing to /person/123
            would update person 123

            But in WheelCMS's case, there's no explicit resource; the resource
            under which a new object is to be created ("the parent") can be
            any existing object.

            This is solved by explicitly posting a create to
              /..parent../create
            where ..parent.. is available as self.instance
        """
        if type is None:
            return self.badrequest()

        if not self.hasaccess():
            return self.forbidden()

        typeinfo = type_registry.get(type)
        formclass = typeinfo.form

        parent = self.parent or self.instance
        if parent and parent.path:
            parentpath = parent.path
        else:
            parentpath = '/'

        self.context['redirect_cancel'] = parentpath + "?info=Create+canceled"
        self.context['form_action'] = 'create'  ## make it absolute?
        self.context['parent'] = parent

        ## if attach: do not accept slug
        if self.post:
            self.context['form'] = \
            self.form = formclass(data=self.request.POST,
                                  parent=parent,
                                  attach=attach,
                                  reserved=self.reserved(),
                                  files=self.request.FILES)
            if self.form.is_valid():
                target = parent  ## where to redirect to
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
                    target = sub

                ent = stracks.content(p.id, name=p.title)
                ent.log("? (%s) created by ?" % typeinfo.title,
                        stracks.user(self.user()), action=stracks.create())

                return self.redirect(target.path or '/',
                                     success='"%s" created' % p.title)
        else:
            self.context['form'] = formclass(parent=parent, attach=attach)
        ## Get spoke model
        self.context['type'] = type

        typeinfo = type_registry.get(type)
        self.context['typeinfo'] = dict(name=typeinfo.name, title=typeinfo.title)

        self.context['attach'] = attach
        self.context['instance'] = self.parent or None # ?? '/' or Node.root()?
        if attach:
            self.context['breadcrumb'] = self.breadcrumb(operation="Attach", details=' "%s"' % typeinfo.title)
        else:
            self.context['breadcrumb'] = self.breadcrumb(operation="Create", details=' "%s"' % typeinfo.title)
        self.context['toolbar'] = Toolbar(self.instance, self.request, status="create")
        return self.template("wheelcms_axle/create.html")

    def update(self):
        action = self.kw.get('action', '')
        if action:
            action_handler = action_registry.get(action, self.instance.path,
                                                 self.spoke())
            if action_handler is None:
                return self.notfound()

            return action_handler(self, self.request, action)

        if not self.hasaccess():
            return self.forbidden()


        instance = self.instance
        content = instance.content()
        parent = instance.parent()

        self.context['redirect_cancel'] = (self.instance.path or '/') + \
                                          "?info=Update+cancelled"
        self.context['toolbar'] = Toolbar(self.instance, self.request, status="edit")

        typename = instance.content().get_name()
        typeinfo = type_registry.get(typename)
        formclass =  typeinfo.form
        slug = instance.slug()

        if self.post:
            self.context['form'] = form = formclass(parent=parent,
                                                    data=self.request.POST,
                                                    reserved=self.reserved(),
                                                    instance=content)

            if form.is_valid():
                form.save()
                ## handle changed slug
                slug = form.cleaned_data.get('slug', None)
                if slug and slug != self.instance.slug():
                    self.instance.rename(slug)

                e = stracks.content(content.id, name=content.title)
                e.log("? (%s) updated by ?" % content.spoke().title,
                      stracks.user(self.user()), action=stracks.edit())
                return self.redirect(instance.path, success="Updated")
        else:
            self.context['form'] = formclass(parent=parent,
                             initial=dict(slug=slug), instance=instance.content())

        self.context['toolbar'].status = 'update'
        self.context['breadcrumb'] = self.breadcrumb(operation="Edit", details=' "%s" (%s)' % (content.title, typeinfo.title))
        return self.template("wheelcms_axle/update.html")


    @context
    def breadcrumb(self, operation="", details=""):
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

            ## If we're in "contents" mode, link to the node's
            ## contents view.

            if operation == "Contents":
                subpath += '/contents'

            path = subpath or '/'

            ## last entry should not get path
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
            res.append((operation + details, ""))

        return res

    def view(self):
        """ frontpage / view """
        spoke = self.spoke()

        if spoke and not spoke.workflow().is_visible():
            if not self.hasaccess():
                return self.forbidden()

        action = self.kw.get('action', '')
        if action:
            action_handler = action_registry.get(action, self.instance.path, spoke)
            if action_handler is None:
                return self.notfound()

            return action_handler(self, self.request, action)


        if self.hasaccess():
            self.context['toolbar'] = Toolbar(self.instance, self.request)
        ## experimental
        if spoke:
            ## update the context with addtional data from the spoke
            self.context.update(spoke.context(self, self.request, self.instance))
            tpl = spoke.view_template()
            ctx = template_registry.context.get((spoke.__class__, tpl))
            if ctx:
                self.context.update(ctx(self, self.request, self.instance))

        if spoke:
            stracks.content(spoke.instance.id,
                            name=spoke.instance.title
                           ).log("? (%s) viewed by ?" % spoke.title,
                                 stracks.user(self.user()),
                                 action=stracks.view())
            return self.template(spoke.view_template())
        return self.template("wheelcms_axle/nospoke.html")

    def list(self):
        self.instance = Node.root()
        return self.view()

    def handle_list(self):
        if not self.hasaccess():
            return self.forbidden()
        self.context['toolbar'] = Toolbar(self.instance, self.request, status="list")
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
        return self.redirect(self.instance.path or '/')

    @json
    @applyrequest
    def handle_reorder(self, rel, target, ref):
        if not self.hasaccess() or not self.post:
            return self.forbidden()
        targetnode = Node.get(target)
        referencenode = Node.get(ref)

        if targetnode is None:
            return self.badrequest()
        if referencenode is None:
            return self.badrequest()
        if targetnode.parent() != self.instance:
            return self.badrequest()
        if referencenode.parent() != self.instance:
            return self.badrequest()

        if rel == "after":
            self.instance.move(targetnode, after=referencenode)
        else:  # before
            self.instance.move(targetnode, before=referencenode)
        return dict(result="ok")

    def handle_contents_actions_delete(self):
        """
            Handle the action buttons from the contents listing:
            paste, delete (cut/copy can be done async)
        """
        if not self.hasaccess() or not self.post:
            return self.forbidden()

        count = 0
        for p in self.request.POST.getlist('selection'):
            n = Node.get(p)
            ## XXX recursively delete, or not, or detach...
            if n:
                content = n.content()
                if content:
                    stracks.content(content.id,
                                name=content.title
                               ).log("? (%s) removed by ?" % content.spoke().title,
                                     stracks.user(self.user()),
                                     action=stracks.delete())
                else:
                    stracks.user(self.user()).log("Unattached node removed: " + n.path, action=stracks.delete());

                try:
                    n.parent().remove(n.slug())
                except NodeNotFound:
                    ## should not happen but if it does, bag it and tag it
                    stracks.content(content.id, name=content.title).exception()

                n.delete()
                count += 1

        return self.redirect(self.instance.path + '/list',
                             info="%d item(s) deleted" % count)

    def handle_popup(self):
        """ popup experiments - #524 """
        return self.template("wheelcms_axle/popup.html", original="/data/powerful-editing")

    @applyrequest
    def handle_panel_selection_details(self, path, type, klass="", title="", target="", download=False):
        """
            type is link of image (later misschien embed, object, whatever)
            link:
             - title
             - target
             - bepaalde props
            image:
             - class (size, float)
             - title/alt
             ..?

            Dit is redelijk generiek, staat los van feitelijke content/spoke. Hooguit een aparte 
            manier van presenteren van content
        """
        # import pdb; pdb.set_trace()
        path = strip_action(path)
        
        node = Node.get(path)
        instance = None
        spoke = None
        if node:
            instance = node.content()
            spoke = instance.spoke()
        
        SIZE_CHOICES = (
            ("img_content_original", "Original"),
            ("img_content_thumb", "Thumb"),
            ("img_content_small", "Small"),
            ("img_content_medium", "Medium"),
            ("img_content_large", "Original"),
        )
        FLOAT_CHOICES = (
            ("img_align_left", "Left"),
            ("img_align_center", "Center"),
            ("img_align_right", "Right")
        )
        ALIGN_CHOICES = (
            ("img_align_top", "Top"),
            ("img_align_middle", "Middle"),
            ("img_align_bottom", "Bottom")
        )

        ## translate klass back to size/float/align
        forminitial = dict(title=title, target=target, download=download)

        klass_parts = klass.split()

        for part in klass_parts:
            if part in [s[0] for s in SIZE_CHOICES]:
                forminitial['size'] = part
            if part in [f[0] for f in FLOAT_CHOICES]:
                forminitial['float'] = part
            if part in [a[0] for a in ALIGN_CHOICES]:
                forminitial['align'] = part

        class PropForm(forms.Form):
            title = forms.CharField()
            if type == "link":
                target = forms.CharField()
                if spoke and isinstance(spoke, FileSpoke):
                    download = forms.BooleanField(help_text="If checked, link will point to "
                                                            "download immediately in stead of File content")
            if type == "image":
                size = forms.ChoiceField(choices=SIZE_CHOICES)
                float = forms.ChoiceField(choices=FLOAT_CHOICES)
                align = forms.ChoiceField(choices=ALIGN_CHOICES)

        propform = PropForm(initial=forminitial)

        return self.template("wheelcms_axle/popup_properties.html", spoke=spoke,
                             instance=instance, mode=type, form=propform)

    @json
    @applyrequest
    def handle_panel(self, path, original, mode):
        return self.panels(path, original, mode)

    def panels(self, path, original, mode):
        """
            Generate panels for the file selection popup
            mode can be either "link" (any content) or "image" (only image
            based content)
        """
        # import pdb; pdb.set_trace()
        
        if not self.hasaccess():
            return self.forbidden()

        ##
        ## No path means a new item is to be selected. Use the current
        ## item as a starting point
        if not path:
            path = self.instance.path

        ## translate / to ""

        if path == "/":
            path = ""
        if original == "/":
            original = ""
        ## remove optional 'action', marked by a +
        ## not sure if this is the right place to do this, or if the browser
        ## modal should have been invoked without the action in the first place


        path = strip_action(path)
        original = strip_action(original)

        node = Node.get(path)
        panels = []

        bookmarks_paths = [""]
        if self.instance.path not in bookmarks_paths:
            bookmarks_paths.append(self.instance.path)
        #if path not in bookmarks_paths:
        #    bookmarks_paths.append(path)
        if original not in bookmarks_paths:
            bookmarks_paths.append(original)

        bookmarks = []

        for p in bookmarks_paths:
            n = Node.get(p)
            content = n.content()
            spoke = content.spoke()
            bookmarks.append(dict(children=[], path=n.path or '/',
                            title=content.title,
                            meta_type=content.meta_type,
                            content=content,
                            icon=spoke.icon_base() + '/' + spoke.icon,
                            spoke=spoke))

        panels.append(
                      self.render_template("wheelcms_axle/popup_links.html",
                                           instance=self.instance,
                                           bookmarks=bookmarks
                                           ))
        # import pdb; pdb.set_trace()
        
        for i in range(2):
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

                content = child.content()

                if not content:
                    continue  ## ignore unattached nodes
                spoke = content.spoke()

                if mode == "link":
                    selectable = True
                elif isinstance(content, ImageContent):
                    selectable = True

                selected = path == child.path or \
                           path.startswith(child.path + '/')
                instance['children'].append(
                                      dict(title=content.title,
                                           path=child.path,
                                           icon=spoke.icon_base() + '/' +
                                                spoke.icon,
                                           selectable=selectable,
                                           meta_type=content.meta_type,
                                           selected=selected))

            panels.insert(1,
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
                              reserved=self.reserved(),
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
        return dict(status="error",
                    errors=dict(storage=self.form.errors['storage'].pop()))


