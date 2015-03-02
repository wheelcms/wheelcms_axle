from django import forms
from django.conf import settings
from django.template import loader, Context
from django.http import HttpResponseServerError, HttpResponseNotFound, Http404
from django.core.urlresolvers import resolve
from django.contrib import messages

from wheelcms_axle.node import Node, NodeNotFound, CantMoveToOffspring
from wheelcms_axle.content import type_registry, ImageContent

from wheelcms_axle.spoke import FileSpoke, Spoke

from wheelcms_axle.utils import get_active_language
from wheelcms_axle.forms import AngularForm

from wheelcms_axle import translate
from wheelcms_axle import locale

from wheelcms_axle import auth

from wheelcms_axle import permissions

from .templates import template_registry
from .actions import action_registry, tabaction

from django.utils import translation
from .models import WheelProfile
from .toolbar import get_toolbar, Toolbar
from .base import WheelView, context
from .utils import applyrequest, json

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


def strip_action(s):
    if '+' in s:
        s = s.split("+", 1)[0].rstrip('/')
    return s

def gethandler(h, name):
    """
        return the handler method identified by 'name'. This
        can be either 'handle_<name>', or name itself if it's
        marked as handler

        XXX deprecate
    """
    if hasattr(h, "handle_" + name):
        return getattr(h, "handle_" + name)
    if hasattr(h, name):
        hh = getattr(h, name)
        if getattr(hh, "ishandler", False):
            return hh
    return None

def handler(f):
    """ identify a method as being able to handle direct calls on a 
        resource, e.g. /person/123/do_foo would map to either handle_do_foo
        or @handler def do_foo()

        XXX deprecate
    """
    f.ishandler = True
    return f

class MainHandler(WheelView):
    instance = None

    """
        Huidige situatie:

        GET op / werkt. Fallthrough url pattern voor reverses is in place.
        coerce_with_request is deels overgenomen; is parent/path setup nog nodig?

    """
    @classmethod
    def resolve(cls, nodepath):
        """ resolve a node path to an actual node in correct language 
            context. """
        ## Do a bit of path normalization: Except for root, start with /,
        ## remove trailing /
        if nodepath in ("/", ""):
            nodepath = ""
        else:
            nodepath = "/{0}".format(nodepath.strip('/'))

        language = get_active_language()

        return Node.get(nodepath, language=language)

    def get(self, request, nodepath=None, handlerpath="", action="", **kw):
        """
            instance - the path to a piece of content
            path - remaining, specifies operation to be invoked.
                   To be deprecated in favor of +actins
        """
        self.is_post = request.method == "POST"
        self.toolbar = get_toolbar()

        ## Why need this?
        # locale.activate_content_language(None)

        self.instance = self.resolve(nodepath)

        ## an action may end in slash: remove it
        if action:
            action = action.rstrip('/')

        language = get_active_language()

        if self.toolbar:
            self.toolbar.instance = self.instance
            self.toolbar.status = Toolbar.VIEW

        if self.instance is None:
            return self.notfound()

        ## make sure the instance is part of the context
        self.context['instance'] = self.instance

        ## pre_handler is to be deprecated. It also depends on self.instance
        self.pre_handler()

        spoke = self.spoke(language=language)
        ## retrieve content type info
        if spoke:
            ## update the context with addtional data from the spoke
            self.context.update(spoke.context(self, self.request,
                                self.instance))
            perm = spoke.permissions.get('view')
        else:
            perm = Spoke.permissions.get('view')

        ## Set default current tab
        self.context['tab_action'] = 'attributes'

        try:
            if handlerpath:
                handler = gethandler(self, handlerpath)
                if handler:
                    return handler()
                return self.notfound()

            if action:
                action_handler = action_registry.get(action, self.instance.path,
                                                 spoke)
                if action_handler is None:
                    return self.notfound()
                ## Should the (decorator for) the action handler do permission checks?
                required_permission = getattr(action_handler, 'permission', perm)
                if not auth.has_access(self.request, spoke, spoke, required_permission):
                    return self.forbidden()

                ## if there's an action, assume it's actually an update action.
                if self.toolbar:
                    self.toolbar.status = Toolbar.UPDATE

                ## Update context if it's a tab action
                if tabaction(action_handler):
                    self.context['tab_action'] = tabaction(action_handler)
                return action_handler(self, request, action)

            if not handlerpath:
                ## special case: post to content means edit/update
                if self.is_post:
                    return self.edit()
                return self.view()
            return self.notfound()
        finally: # XXX Does this work as expected?
            self.post_handler()

    ## GET and POST are treated alike, initially
    post = get

    def active_language(self):
        return get_active_language()

    @context
    def body_class(self):
        if self.instance:
            model = self.instance.primary_content()

            if model:
                typename = model.get_name()
                parts = typename.split(".")
                return " ".join("_".join(parts[:i+1])
                                for i in range(len(parts)))

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
        if self.instance:
            model = self.instance.content(language=language)
            if model:
                return model.spoke()
        return None

    @context
    def tabs(self, spoke=None):
        """ return the tabs / actions the user has access to """
        if not spoke and self.instance and self.instance.content():
            spoke = self.spoke()

        if spoke:
            return [tab for tab in spoke.tabs()
                    if auth.has_access(self.request, spoke, spoke,
                                       tab.get('permission',
                                               permissions.edit_content))]

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

    def pre_handler(self):
        """ invoked before a method """

        ## if user authenticated, find language setting, activate it.
        ## Will only work for requests that go through this handler
        self._stored_language = None
        current_language = translation.get_language()

        if self.request.user.is_authenticated():
            try:
                language = self.request.user.my_profile.language
                if language and language != current_language:
                    ## store the content language
                    self._stored_language = current_language
                    locale.activate_content_language(current_language)
                    translation.activate(language)
                    ## coercion has taken place before the switch,
                    ## so self.instance will be initialized to the old
                    ## language. Update it!
                    #if self.instance:
                    #    self.instance.preferred_language = language
            except WheelProfile.DoesNotExist:
                pass
        else:
            locale.activate_content_language(current_language)

    def post_handler(self):
        if self._stored_language:
            translation.activate(self._stored_language)

    @classmethod
    def reserved(cls):
        ## XXX Can be mostly deprecated once handlers -> actions
        return set(["create", "update", "list"] + \
               [x[7:] for x in dir(cls) if x.startswith("handle_")] + \
               [x for x in dir(cls) if getattr(getattr(cls, x), "ishandler", False)])

    def view(self):
        """ frontpage / view """
        language = self.active_language()
        spoke = self.spoke(language=language)


        if spoke:
            ## update the context with addtional data from the spoke
            self.context.update(spoke.context(self, self.request,
                                self.instance))
            perm = spoke.permissions.get('view')
        else:
            perm = Spoke.permissions.get('view')

        if not auth.has_access(self.request, spoke, spoke, perm):
            return self.forbidden()


        if spoke:
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

        ##if not self.hasaccess():
        ##   return self.forbidden()

        typeinfo = type_registry.get(type)
        perm = typeinfo.permissions.get('create')
        # alternatives:
        # typeinfo.has_access('edit', request)
        # ... on instance?
        if not auth.has_access(self.request, typeinfo, None, perm):
            return self.forbidden()

        formclass = typeinfo.form

        parent = self.instance
        parentpath = parent.get_absolute_url()

        self.context['redirect_cancel'] = parentpath + "?info=Create+canceled"
        self.context['form_action'] = 'create'  ## make it absolute?

        ## Hide tabs since we're creating new content
        self.context['tabs'] = ()

        ## if attach: do not accept slug
        if self.is_post:
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

                    ## force reindex
                    typeinfo.model.objects.get(pk=p.pk).save()

                    ent = stracks.content(p.id, name=p.title)
                    ent.log("? (%s) created by ?" % typeinfo.title,
                            stracks.user(self.user()), action=stracks.create())

                    return self.redirect(target.get_absolute_url(),
                                         success='"%s" created' % p.title)
                except OSError, e:
                    messages.error("An error occured while saving: %s" % str(e))
        else:
            default_language = typeinfo.default_language

            self.context['form'] = formclass(parent=parent, attach=attach, initial=dict(language=default_language or language))
        ## Get spoke model
        self.context['type'] = type

        typeinfo = type_registry.get(type)
        self.context['typeinfo'] = dict(name=typeinfo.name, title=typeinfo.title)

        self.context['attach'] = attach
        if attach:
            self.context['breadcrumb'] = self.breadcrumb(operation="Attach", details=' "%s"' % typeinfo.title)
        else:
            self.context['breadcrumb'] = self.breadcrumb(operation="Create", details=' "%s"' % typeinfo.title)
        if self.toolbar:
            self.toolbar.status = Toolbar.CREATE

        template = typeinfo.create_template(self.request, parent)

        return self.template(template)

    @handler
    def edit(self):
        language = self.active_language()

        instance = self.instance

        supported_languages = (l[0] for l in translate.languages())
        if language not in supported_languages:
            return self.redirect(instance.get_absolute_url(),
                                 error="Unsupported Language")

        if self.spoke():
            ## update the context with addtional data from the spoke
            self.context.update(self.spoke().context(self, self.request,
                                self.instance))


        content = instance.content(language=language)
        create_translation = False

        if content is None:
            pcontent = instance.primary_content()
            typename = pcontent.get_name()
            typeinfo = type_registry.get(typename)
            create_translation = True
            spoke = pcontent.spoke()
        else:
            typename = content.get_name()
            typeinfo = type_registry.get(typename)
            spoke = content.spoke()

        perm = typeinfo.permissions.get('edit')

        if not auth.has_access(self.request, typeinfo, spoke, perm):
            return self.forbidden()

        # reset tabs with current language tabs
        self.context['tabs'] = self.tabs(spoke)

        parent = instance.parent()

        self.context['redirect_cancel'] = self.instance.get_absolute_url() + \
                                          "?info=Update+cancelled"
        if self.toolbar:
            self.toolbar.status = Toolbar.UPDATE

        formclass =  typeinfo.form
        slug = instance.slug(language=language)

        if self.is_post:
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
                    if create_translation:
                        content = form.save(commit=False)
                    else:  # ordinary update
                        content = form.save()
                except OSError, e:
                    messages.error("An error occured while saving: %s" % str(e))

                if create_translation:
                    if self.user().is_authenticated():
                        content.owner = self.user()
                    content.node = self.instance
                    content.save()
                    form.save_m2m()

                ## handle changed slug
                slug = form.cleaned_data.get('slug', None)
                content_language = form.cleaned_data.get('language', settings.FALLBACK)


                if slug and slug != self.instance.slug(language=content_language):
                    self.instance.rename(slug, language=content_language)

                e = stracks.content(content.id, name=content.title)
                e.log("? (%s) updated by ?" % content.spoke().title,
                      stracks.user(self.user()), action=stracks.edit())
                return self.redirect(instance.get_absolute_url(),
                                     success="Updated")
        else:
            args = dict(parent=parent,
                        initial=dict(slug=slug),
                        skip_slug=self.instance.isroot())
            if content:
                # updating existing content
                args['instance'] = content
            else:
                # translating new content. Make sure its language is set to
                # the active language
                args['initial']['language'] = language
            self.context['form'] = formclass(**args)

        if create_translation:
            primary_content = self.instance.primary_content()
            ## there must be primary content, else the node would be unattached
            title = primary_content.title
            self.context['breadcrumb'] = self.breadcrumb(operation="Translate",
                                details=' "%s" (%s)' % (title, typeinfo.title))
        else:
            self.context['breadcrumb'] = self.breadcrumb(operation="Edit",
                        details=' "%s" (%s)' % (content.title, typeinfo.title))
        template = spoke.update_template()
        return self.template(template)


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

    def list(self):
        self.instance = Node.root()
        return self.view()

    def handle_list(self):
        spoke = self.spoke()

        if spoke:
            perm = spoke.permissions.get('list')
        else:
            perm = Spoke.permissions.get('list')

        if not auth.has_access(self.request, spoke, spoke, perm):
            return self.forbidden()

        if self.toolbar:
            self.toolbar.status = Toolbar.LIST
        self.context['breadcrumb'] = self.breadcrumb(operation="Contents")

        self.context['can_paste'] = \
            len(self.request.session.get('clipboard_copy', [])) + \
            len(self.request.session.get('clipboard_cut', []))

        active = self.active_language()

        children = []

        for child in self.instance.children():
            c = dict(node=child, active=None, translations=[], ipath=child.tree_path)
            for lang, langtitle in translate.languages():
                langcontent = child.content(language=lang)
                c["translations"].append((lang, langcontent,
                                          "switch_admin_language?path=" + child.tree_path + "&switchto=" + lang + "&rest=edit"))
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
        if self.spoke() and self.spoke().allowed_spokes():
            return self.redirect(self.instance.get_absolute_url() + 'list')
        return self.redirect(self.instance.get_absolute_url())

    @json
    @applyrequest
    def handle_reorder(self, rel, target, ref):
        if not self.hasaccess() or not self.is_post:
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
        if not self.hasaccess() or not self.is_post:
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
        if not self.hasaccess() or not self.is_post:
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

    @json
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
            ("img_content_large", "Large"),
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
        forminitial = dict(title=default_title, target=target, download=download,
                           size=SIZE_CHOICES[-1][0],
                           float=FLOAT_CHOICES[1][0],
                           align=ALIGN_CHOICES[0][0])

        ## if not target, determine local/new based on locality of url
        if not forminitial['target']:
            if path:
                forminitial['target'] = "_self"
            else:
                forminitial['target'] = "_blank"
        klass_parts = klass.split()

        for part in klass_parts:
            if part in [s[0] for s in SIZE_CHOICES]:
                forminitial['size'] = part
            if part in [f[0] for f in FLOAT_CHOICES]:
                forminitial['float'] = part
            if part in [a[0] for a in ALIGN_CHOICES]:
                forminitial['align'] = part

        class PropForm(AngularForm):
            ng_ns = "propsform"

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

        return dict(initialdata=forminitial,
                    template=self.render_template("wheelcms_axle/popup_properties.html", spoke=spoke,
                             instance=instance, mode=type, form=propform))

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

        ##
        ## Selectable means the node is a valid selection. Unattached
        ## nodes are never selectable and in image mode only image based
        ## content is a valid selection
        def is_selectable(node):
            content = node.content()
            if content:
                if mode == "link":
                    return True
                elif isinstance(content, ImageContent):
                    return True
            return False

        ## Is the starting point a valid selection?
        start_selectable = is_selectable(node)

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
            selectable = is_selectable(n)
            bookmarks.append(dict(children=[], path=n.get_absolute_url(),
                            title=content.title,
                            meta_type=content.meta_type,
                            content=content,
                            selectable=selectable,
                            icon=spoke.icon_base() + '/' + spoke.icon,
                            spoke=spoke))

        panels.append(self.render_template("wheelcms_axle/popup_links.html",
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
                content = child.content()

                if not content:
                    continue  ## ignore unattached nodes
                spoke = content.spoke()

                selectable = is_selectable(child)

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
            content = node.content()
            selectable = is_selectable(node)
            if node.isroot():
                crumbs.insert(0, dict(path=node.get_absolute_url(),
                                      selectable=selectable, title="Home"))
                break
            crumbs.insert(0, dict(path=node.get_absolute_url(),
                                  selectable=selectable,
                                  title=node.content().title))
            node = node.parent()

        crumbtpl = self.render_template("wheelcms_axle/popup_crumbs.html",
                                        crumbs=crumbs)
        print "SEL ", path,  start_selectable
        return dict(panels=panels, path=start.get_absolute_url(),
                    crumbs=crumbtpl, upload=upload, selectable=start_selectable)

    @json
    @applyrequest
    def handle_fileup(self, type):
        if not self.hasaccess():
            return self.forbidden()

        formclass = type_registry.get(type).light_form

        parent = self.instance

        ## use get() to return type-specific rendered light-form?

        if not self.is_post:
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

        ## for now, assume that if something went wrong,
        ## it's with the uploaded file
        error = "Unknown error"
        if 'storage' in self.form.errors:
            error = self.form.errors['storage'].pop()
        return dict(status="error", errors=error)


    @applyrequest
    def handle_switch_admin_language(self, switchto, path=None, rest=""):
        if not self.hasaccess():
            return self.forbidden()

        locale.activate_content_language(switchto)

        if path:
            node = Node.objects.get(tree_path=path)
        else:
            node = self.instance

        return self.redirect(node.get_absolute_url(language=switchto) + rest,
                             info="Switched to %s" % switchto)

