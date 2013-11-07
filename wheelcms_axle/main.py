from django import forms
from django.conf import settings
from django.template import loader, Context
from django.http import HttpResponseServerError, HttpResponseNotFound, Http404
from django.core.urlresolvers import resolve

from two.ol.base import RESTLikeHandler, applyrequest, context, json, handler
from wheelcms_axle.node import Node, NodeNotFound, CantMoveToOffspring
from wheelcms_axle.content import type_registry, Content, ImageContent

from wheelcms_axle.spoke import FileSpoke

from wheelcms_axle.toolbar import Toolbar

from wheelcms_axle.base import WheelHandlerMixin
from wheelcms_axle.utils import get_active_language
from wheelcms_axle import translate

from .templates import template_registry
from .actions import action_registry

import stracks


from wheelcms_axle import context_processors

def resolve_path(p):
    """
        The path we receive from javascript code will include possible settings 
        specific url prefix (e.g. /blog).
        This method will attempt to resolve that into an ordinary Node path
    """
    ## first of all, strip optional path

    try:
        ## resolve() should be able to resolve a url with an action, e.g.
        ## /blog/some/path/foo.jpg/+download
        ## but for some reason it 404's XXX
        ## e.g. resolve("/blog/some/path/foo.jpg/+download")
        p = p.rsplit("+", 1)[0]  ## remove action

        ## make sure it ends in a / because that's what django likes
        ## (possibly related to the REDIRECT_URL setting?)
        if not p.endswith('/'):
            p = p + '/'
        m = resolve(p)
        if 'instance' in m.kwargs:
            resolved = m.kwargs['instance'].rstrip('/')
            if resolved:
                return '/' + resolved
            return '' # root
    except Http404:
        return None

def wheel_error_context(request):
    """
        Provide enough context for the 404/500 template (and more specifically
        its base) to render correctly.
    """

    context = Context()
    context['request'] = request
    context['user'] = request.user
    context.update(context_processors.configuration(request))
    return context

def wheel_404(request):
    """ alternative 404 page """
    t = loader.get_template("wheelcms_axle/404.html")

    return HttpResponseNotFound(t.render(wheel_error_context(request)))


def wheel_500(request):
    """ alternative 500 page """
    t = loader.get_template("wheelcms_axle/500.html")

    return HttpResponseServerError(t.render(wheel_error_context(request)))


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

    def active_language(self):
        return get_active_language(self.request)

    @context
    def body_class(self):
        if self.instance:
            model = self.instance.primary_content()

            if model:
                typename = model.get_name()
                parts = typename.split(".")
                return " ".join("_".join(parts[:i+1]) for i in range(len(parts)))

        return ""

    @context
    def page_title(self, language=None):
        """ return the content title, if any """
        language = language or self.active_language()
        if self.instance:
            content = self.instance.content(language=language)
            if content:
                return content.title
        return "Unattached node"

    @context
    def spoke(self, language=None):
        """ return type info for the current content, if any """
        language = language or self.active_language()
        model = self.instance.content(language=language)
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
    def content(self, language=None):
        """ return the actual content for the node / spoke """
        language = language or self.active_language()
        modelinstance = self.instance.content(language=language)
        if modelinstance:
            return modelinstance
        return None

    @context
    def languages(self):
        """ return language switch options """
        if not self.instance:
            return None

        ## If there is not more that one language defined, don't show
        ## a selector
        if len(settings.LANGUAGES) <= 1:
            return None

        res = []
        ld = getattr(settings, 'LANGUAGE_DOMAINS', {})
        current_language = self.active_language()
        current_label = dict(settings.LANGUAGES).get(current_language, current_language)

        for lang, label in settings.CONTENT_LANGUAGES:
            if lang == current_language:
                is_current = True
            else:
                is_current = False

            langcontent = self.instance.content(language=lang)
            if langcontent:
                url = langcontent.get_absolute_url()
                has_translation = True
            else:
                url = Node.root().get_absolute_url(language=lang)
                has_translation = False

            domain = ld.get(lang)
            if domain:
                protocol = "https" if self.request.is_secure() else "http"
                url = "%s://%s%s" % (protocol, domain, url)

            res.append(dict(id=lang, label=label, url=url,
                            has_translation=has_translation,
                            is_current=is_current))

        return dict(current=dict(id=current_language,
                                 label=current_label),
                    languages=res)

    def formclass(self, data=None, instance=None):
        """
            Invoked by dispatcher to initialize this handler's form.
            But since we need more context to properly initialize, don't
            do it here and return None in stead. If you need a form instance,
            create it explicitly
        """

        return None

    @classmethod
    def coerce_with_request(cls, i, request=None):
        """
            coerce either a parent and instance, a parent or an instance.
            If there's both a parent and an instance, the instance is relative
            to the parent, so resolving needs to be done by combing them

            We're supporting the parent/instance combo (somewhat) but don't
            really need it - <instance>/update works fine, and no instance is
            required for /create
        """
        language = get_active_language(request)

        d = dict()

        parent_path = ""
        if i.get('parent') is not None:
            parent_path = i['parent']
            if parent_path:
                parent_path = '/' + parent_path
            parent = d['parent'] = Node.get(parent_path, language=language)
            if parent is None:
                return cls.notfound()

        if i.get('instance') is not None:
            instance_path = i['instance']
            if not instance_path:  ## it can be ""
                path = parent_path
            else:
                path = parent_path + "/" + instance_path

            d['instance'] = instance = Node.get(path, language=language)

            if instance is None:
                return cls.notfound()
        return d

    ## XXX something should be deprecated here. Tests still depend
    ## on requestless coerce()
    coerce = coerce_with_request

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
        language = self.active_language()

        if type is None:
            return self.badrequest()

        if not self.hasaccess():
            return self.forbidden()

        typeinfo = type_registry.get(type)
        formclass = typeinfo.form

        parent = self.parent or self.instance
        if parent and parent.path:
            parentpath = parent.get_absolute_url()
        else:
            parentpath = Node.root().get_absolute_url()

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
                try:
                    p.save()

                    self.form.save_m2m()
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

                    return self.redirect(target.get_absolute_url(),
                                         success='"%s" created' % p.title)
                except OSError, e:
                    self.context['error_message'] = "An error occured " \
                            "while saving: %s" % str(e)
        else:
            default_language = typeinfo.default_language

            self.context['form'] = formclass(parent=parent, attach=attach, initial=dict(language=default_language or language))
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
        language = self.active_language()

        instance = self.instance

        supported_languages = (l[0] for l in translate.languages())
        if language not in supported_languages:
            return self.redirect(instance.get_absolute_url(),
                                 error="Unsupported Language")

        if action:
            ## match against path, not get_absolute_url which is configuration specific
            action_handler = action_registry.get(action, self.instance.path,
                                                 self.spoke())
            if action_handler is None:
                return self.notfound()

            return action_handler(self, self.request, action)

        if not self.hasaccess():
            return self.forbidden()


        content = instance.content(language=language)
        create_translation = False

        if content is None:
            pcontent = instance.primary_content()
            typename = pcontent.get_name()
            typeinfo = type_registry.get(typename)
            create_translation = True
        else:
            typename = content.get_name()
            typeinfo = type_registry.get(typename)

        parent = instance.parent()

        self.context['redirect_cancel'] = self.instance.get_absolute_url() + \
                                          "?info=Update+cancelled"
        self.context['toolbar'] = Toolbar(self.instance, self.request, status="edit")

        formclass =  typeinfo.form
        slug = instance.slug(language=language)

        if self.post:
            args = dict(parent=parent, data=self.request.POST,
                        reserved=self.reserved(),
                        skip_slug=self.instance.isroot(),
                        node=self.instance,
                        files=self.request.FILES)
            if content:
                args['instance'] = content

            self.context['form'] = form = formclass(**args)

            if form.is_valid():
                try:
                    content = form.save()
                except OSError, e:
                    self.context['error_message'] = "An error occured " \
                            "while saving: %s" % str(e)

                if create_translation:
                    if self.user().is_authenticated():
                        content.user = self.user()
                    content.node = self.instance
                    content.save()

                ## handle changed slug
                slug = form.cleaned_data.get('slug', None)
                content_language = form.cleaned_data.get('language', settings.FALLBACK)


                if slug and slug != self.instance.slug(language=content_language):
                    self.instance.rename(slug, language=content_language)

                e = stracks.content(content.id, name=content.title)
                e.log("? (%s) updated by ?" % content.spoke().title,
                      stracks.user(self.user()), action=stracks.edit())
                return self.redirect(instance.get_absolute_url(), success="Updated")
        else:
            args = dict(parent=parent,
                        initial=dict(slug=slug),
                        skip_slug=self.instance.isroot())
            if content:
                # updating existing content
                args['instance'] = content
            else:
                # translating new content. Make sure its language is set to the active
                # language
                args['initial']['language'] = language
            self.context['form'] = formclass(**args)

        self.context['toolbar'].status = 'update'
        if create_translation:
            primary_content = self.instance.primary_content()
            ## there must be primary content, else the node would be unattached
            title = primary_content.title
            self.context['breadcrumb'] = self.breadcrumb(operation="Translate", details=' "%s" (%s)' % (title, typeinfo.title))
        else:
            self.context['breadcrumb'] = self.breadcrumb(operation="Edit", details=' "%s" (%s)' % (content.title, typeinfo.title))
        return self.template("wheelcms_axle/update.html")


    @context
    def breadcrumb(self, operation="", details=""):
        """ generate breadcrumb path. """
        language = self.active_language()

        base = self.instance or self.parent
        if not base:
            ## parent
            return []

        parts = base.get_path(language=language).split("/")
        res = []
        for i in range(len(parts)):
            subpath = "/".join(parts[:i+1])
            node = Node.get(subpath, language=language)
            content = node.content(language=language)
            primary_content = node.primary_content()

            ## If we're in "contents" mode, link to the node's
            ## contents view.

            if operation == "Contents":
                subpath += '/contents'

            path = node.get_absolute_url()

            ## last entry should not get path
            if not operation:
                if i == len(parts) - 1:
                    path = ""

            if node.isroot():
                if primary_content and not content:
                    title = "Home (untranslated)"
                elif content:
                    title = "Home"
                else:
                    title = "Unattached rootnode"
            else:
                if primary_content and not content:
                    title = 'Untranslated content "%s"' % primary_content.title
                elif not content:
                    title = "Unattached node %s" % (subpath or '/')
                else:
                    title = content.title

            res.append((title, path))

        if operation:
            res.append((operation + details, ""))

        return res

    def view(self):
        """ frontpage / view """
        language = self.active_language()
        spoke = self.spoke(language=language)

        if spoke and not spoke.workflow().is_visible():
            if not self.hasaccess():
                return self.forbidden()

        action = self.kw.get('action', '')
        if action:
            ## again, use node's path directly, not get_absolute_url, which is
            ## configuration specific
            action_handler = action_registry.get(action, self.instance.path, spoke)
            if action_handler is None:
                return self.notfound()

            return action_handler(self, self.request, action)


        if self.hasaccess():
            self.context['toolbar'] = Toolbar(self.instance, self.request)

        if spoke:
            ## update the context with addtional data from the spoke
            self.context.update(spoke.context(self, self.request, self.instance))
            tpl = spoke.view_template()
            ctx = template_registry.context.get((spoke.__class__, tpl))
            if ctx:
                self.context.update(ctx(self, self.request, self.instance))

            stracks.content(spoke.instance.id,
                            name=spoke.instance.title
                           ).log("? (%s) viewed by ?" % spoke.title,
                                 stracks.user(self.user()),
                                 action=stracks.view())
            return self.template(spoke.view_template())
        elif self.instance.primary_content():
            """ attached but untranslated """
            if self.hasaccess():
                return self.redirect(self.instance.get_absolute_url(language=language) + "edit",
                    info="This content is not available in this language")
            elif self.instance.isroot():
                return self.template("wheelcms_axle/notranslation.html")

            return self.notfound()

        return self.template("wheelcms_axle/nospoke.html")

    def list(self):
        self.instance = Node.root()
        return self.view()

    def handle_list(self):
        if not self.hasaccess():
            return self.forbidden()
        self.context['toolbar'] = Toolbar(self.instance, self.request,
                                          status="list")
        self.context['breadcrumb'] = self.breadcrumb(operation="Contents")
        spoke = self.spoke()

        self.context['can_paste'] = \
            len(self.request.session.get('clipboard_copy', [])) + \
            len(self.request.session.get('clipboard_cut', []))

        active = self.active_language()

        children = []

        for child in self.instance.children():
            c = dict(active=None, translations=[], ipath=child.tree_path)
            for lang, langtitle in translate.languages():
                langcontent = child.content(language=lang)
                c["translations"].append((lang, langcontent,
                                          "switch_admin_language?path=" + child.tree_path + "&language=" + lang + "&rest=edit"))
                if lang == active:
                    c["active"] = langcontent
            if not c['active']:
                c['active'] = child.primary_content()
            children.append(c)

        self.context['children'] = children

        if spoke:
            return self.template(spoke.list_template())

        return self.template("wheelcms_axle/contents.html")

    def handle_contents(self):
        """ handle the /contents method. Usually this will give a listing
            of child-content, but in certain cases this makes no sense (e.g.
            childless content, or content that simply can't have children.

            This also may behave differently depending on the user's access
        """
        if self.spoke() and self.spoke().addable_children():
            return self.redirect(self.instance.get_absolute_url() + 'list')
        return self.redirect(self.instance.get_absolute_url())

    @json
    @applyrequest
    def handle_reorder(self, rel, target, ref):
        if not self.hasaccess() or not self.post:
            return self.forbidden()
        
        targetnode = Node.objects.get(tree_path=target)
        referencenode = Node.objects.get(tree_path=ref)

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

    def handle_contents_actions_cutcopypaste(self):
        """ handle cut/copy/paste of items """
        if not self.hasaccess() or not self.post:
            return self.forbidden()

        action = self.request.POST.get('action')
        raw_selection = self.request.POST.getlist('selection', [])

        selection = []
        for p in raw_selection:
            if p and Node.objects.get(tree_path=p):
                selection.append(p)

        count = len(selection)

        if action == "cut":
            self.request.session['clipboard_copy'] = []
            self.request.session['clipboard_cut'] = selection


            return self.redirect(self.instance.get_absolute_url() + 'list',
                                 info="%d item(s) added to clipboard for move" % count)
        elif action == "copy":
            self.request.session['clipboard_cut'] = []
            self.request.session['clipboard_copy'] = selection
            return self.redirect(self.instance.get_absolute_url() + 'list',
                                 info="%d item(s) added to clipboard for copy" % count)
        elif action == "paste":
            copy = False
            clipboard_copy = self.request.session.get('clipboard_copy', [])
            clipboard_cut = self.request.session.get('clipboard_cut', [])
            clipboard = []

            if clipboard_copy:
                copy = True
                clipboard = clipboard_copy
            elif clipboard_cut:
                copy = False
                clipboard = clipboard_cut

            accum_success = []
            accum_failure = []

            # import pdb; pdb.set_trace()
            
            for p in clipboard:
                n = Node.objects.get(tree_path=p)
                if n:
                    try:
                        base, success, failure = self.instance.paste(n, copy=copy)
                        accum_success.extend(success)
                        accum_failure.extend(failure)
                    except CantMoveToOffspring:
                        accum_failure.append((p, "Can't move to self or offspring"))


            self.request.session['clipboard_copy'] = []
            self.request.session['clipboard_cut'] = []
            count = len(accum_success)
            if copy:
                info = "%d item(s) copied" % count
            else:
                info = "%d item(s) moved" % count

            return self.redirect(self.instance.get_absolute_url() + 'list',
                                 info=info)



        return self.redirect(self.instance.get_absolute_url() + 'list')

    def handle_contents_actions_delete(self):
        """
            Handle the action buttons from the contents listing:
            paste, delete (cut/copy can be done async)
        """
        if not self.hasaccess() or not self.post:
            return self.forbidden()

        count = 0
        for p in self.request.POST.getlist('selection'):
            n = Node.objects.get(tree_path=p)
            ## XXX recursively delete, or not, or detach...
            if n:
                content = n.content()
                if content:
                    stracks.content(content.id,
                                name=content.title
                               ).log("? (%s) removed by ?" %
                                     content.spoke().title,
                                     stracks.user(self.user()),
                                     action=stracks.delete())
                else:
                    stracks.user(self.user()).log("Unattached node removed: "
                                                  + n.get_absolute_url(),
                                                  action=stracks.delete());

                try:
                    n.parent().remove(n.slug())
                except NodeNotFound:
                    ## should not happen but if it does, bag it and tag it
                    stracks.content(content.id, name=content.title).exception()

                n.delete()
                count += 1

        return self.redirect(self.instance.get_absolute_url() + 'list',
                             info="%d item(s) deleted" % count)

    @applyrequest
    def handle_panel_selection_details(self, path, type, klass="", title="",
                                       target="", download=False,
                                       newselection=False):
        """
            Setup the panel to configure a link/image insert
        """
        ## resolve relative / prefixed url to absolute node path
        path = resolve_path(path)

        node = Node.get(path)
        instance = None
        spoke = None
        default_title = title

        if node:
            instance = node.content()
            spoke = instance.spoke()
            if newselection:
                default_title = instance.title

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

        TARGET_CHOICES = (
            ("_self", "Same window"),
            ("_blank", "New window"),
        )
        ## _parent and _top are not sensible options, nor is an explicit
        ## framename

        ## translate klass back to size/float/align
        forminitial = dict(title=default_title, target=target, download=download)

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
                target = forms.ChoiceField(choices=TARGET_CHOICES,
                                           initial="_self",
                         help_text="Where should the link open in when clicked?")
                if spoke and isinstance(spoke, FileSpoke):
                    download = forms.BooleanField(
                                help_text="If checked, link will point to "
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
        language = self.active_language()
        if not self.hasaccess():
            return self.forbidden()

        ##
        ## No path means a new item is to be selected. Use the current
        ## item as a starting point
        
        if not path:
            path = self.instance.path
        else:
            path = resolve_path(path)

        if path is None:
            return self.notfound()

        original = resolve_path(original) or ""

        ## remove optional 'action', marked by a +
        ## not sure if this is the right place to do this, or if the browser
        ## modal should have been invoked without the action in the first place


        path = strip_action(path)
        original = strip_action(original)

        node = start = Node.get(path)# , language=language)
        panels = []

        ## first panel: bookmarks/shortcuts

        bookmarks_paths = [''] # root
        if self.instance.path not in bookmarks_paths:
            bookmarks_paths.append(self.instance.path)
        #if path not in bookmarks_paths:
        #    bookmarks_paths.append(path)
        ## original can also be an external url, starting with http
        if original not in bookmarks_paths and not original.startswith("http"):
            bookmarks_paths.append(original)

        bookmarks = []

        for p in bookmarks_paths:
            ## handle non-existing nodes and unattached nodes
            n = Node.get(p)
            if not n:
                continue
            content = n.content()
            if not content: ## unattached
                continue
            spoke = content.spoke()
            bookmarks.append(dict(children=[], path=n.get_absolute_url(),
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
        upload = False

        for i in range(2):
            content = node.content()

            if content:
                ## FileSpoke also includes ImageSpoke

                spoke = content.spoke()
                addables = [x for x in spoke.addable_children()
                            if issubclass(x, FileSpoke)]
                instance = dict(children=[], path=node.get_absolute_url(),
                                title=content.title,
                                meta_type=content.meta_type,
                                content=content,
                                spoke=spoke,
                                addables=addables)
            else:
                addables = [x for x in type_registry.values()
                            if issubclass(x, FileSpoke)]
                instance = dict(children=[], path=node.get_absolute_url(),
                                title="Unattached node",
                                meta_type="none",
                                content=None,
                                spoke=None,
                                addables=addables)

            if i == 0:
                ## first iteration means current context. Check if uploading
                ## is possible.
                upload = bool(addables)

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
                                           path=child.get_absolute_url(),
                                           icon=spoke.icon_base() + '/' +
                                                spoke.icon,
                                           selectable=selectable,
                                           meta_type=content.meta_type,
                                           selected=selected))

            panels.insert(1,
                          self.render_template("wheelcms_axle/popup_list.html",
                                               instance=instance,
                                               path=node.get_absolute_url(),
                                               mode=mode,
                                               selectable=(i==0)))
            if node.isroot():
                break
            node = node.parent()

        ## generate the crumbs
        crumbs = []
        node = start
        while True:
            if node.isroot():
                crumbs.insert(0, dict(path=node.get_absolute_url(), title="Home"))
                break
            crumbs.insert(0, dict(path=node.get_absolute_url(),
                                  title=node.content().title))
            node = node.parent()

        crumbtpl = self.render_template("wheelcms_axle/popup_crumbs.html",
                                        crumbs=crumbs)
        return dict(panels=panels, path=start.get_absolute_url(),
                    crumbs=crumbtpl, upload=upload)

    @json
    @applyrequest
    def handle_fileup(self, type):
        if not self.hasaccess():
            return self.forbidden()

        formclass = type_registry.get(type).light_form

        parent = self.instance

        ## use get() to return type-specific rendered light-form?

        if not self.post:
            form = formclass(parent=parent)
            if 'state' in form.fields:
                form.fields['state'].initial = 'visible'  ## XXX BIG HACK ALERT. Issue 659
            return dict(form=self.render_template("wheelcms_axle/popup_upload.html",
                                                  form=form,
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
            if not p.language:
                p.language = 'any'
            if self.user().is_authenticated():
                p.owner = self.user()
            try:
                p.save()
            except OSError, e:
                return dict(status="error",
                            errors=dict(storage="An error occured while "
                                        "saving: %s" % str(e)))
            self.form.save_m2m()
            slug = self.form.cleaned_data['slug']
            sub = parent.add(slug)
            sub.set(p)
            return dict(status="ok", path=sub.get_absolute_url())

        ## for now, assume that if something went wrong, it's with the uploaded file
        return dict(status="error",
                    errors=dict(storage=self.form.errors['storage'].pop()))


    @applyrequest
    def handle_switch_admin_language(self, language, path=None, rest=""):
        if not self.hasaccess():
            return self.forbidden()

        self.request.session['admin_language'] = language
        if path:
            node = Node.objects.get(tree_path=path)
        else:
            node = self.instance

        return self.redirect(node.get_absolute_url(language=language) + rest,
                             info="Switched to %s" % language)

