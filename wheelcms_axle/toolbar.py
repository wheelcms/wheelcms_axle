import urllib2

from django.conf import settings

from wheelcms_axle.content import type_registry
from wheelcms_axle.node import Node
from wheelcms_axle.workflows.default import worklist as default_worklist
from wheelcms_axle import access
from wheelcms_axle.utils import get_active_language
from wheelcms_axle import translate

from threading import local

_toolbar_storage = local()

def create_toolbar(request, force=False):
    try:
        if not force:
            return _toolbar_storage.toolbar
    except AttributeError:
        pass

    _toolbar_storage.toolbar = Toolbar(Node.root(), request=request,
                                       status="special")
    return _toolbar_storage.toolbar

def get_toolbar():
    try:
        return _toolbar_storage.toolbar
    except AttributeError:
        return None

class Toolbar(object):
    """
        Wrap toolbar-related data, functionality

        Possible toolbar/context states:
        view - viewing content
        update - updating content
        list - listing content
        create - creating content
        special - not in a content-context
    """
    VIEW = "view"
    UPDATE = "update"
    LIST = "list"
    CREATE = "create"
    SPECIAL = "special"
    ATTACH = "attach"

    def __init__(self, instance, request, status=VIEW):
        self.instance = instance
        self.request = request
        self.status = status

        self.actions = []

    def addAction(self, action):
        self.actions.append(action)


    def type(self):
        if not (self.instance and self.instance.content()):
            return None

        return type_registry.get(self.instance.content().get_name())

    def single_child(self):
        """ return the single child if there's only one, else None.
            This allows for a create button in stead of a dropup
        """
        type = self.type()
        if type is None:
            return None
        if len(type.children) == 1:
            return type.children[0]
        return None

    def primary(self):
        """ return type details for this type's primary content, if any """
        type = self.type()
        if type is None:
            ## unconnected
            return None

        p = type.primary

        if p:
            return dict(name=p.name(),
                        title=p.title,
                        icon_path=p.full_type_icon_path())
        return None

    def children(self):
        """ return the addable children for this type, except the primary
            type (if any) """
        type = self.type()
        ## order?
        ## unconnected, or no restrictions
        if type is None:
            ch = [t for t in type_registry.values() if t.implicit_add]
            primary = None
        else:
            ch = type(self.instance.content()).allowed_spokes()
            primary = type.primary

        
        return [dict(name=c.name(),
                     title=c.title,
                     icon_path=c.full_type_icon_path())
                for c in ch if c != primary]

    def show_create(self):
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        ## do not show when creating or updating
        if self.status in (Toolbar.CREATE, Toolbar.UPDATE):
            return False
        if self.type() is None:
            return True
        if self.type().children is None:
            return True
        return bool(self.type().children)

    def show_update(self):
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        ## do not show when creating or updating
        if self.status in ("update", "create"):
            return False
        if not (self.instance and self.instance.content()):
            return False
        return True

    def show_translate(self):
        """
            The translate button is shown on pages that are not available
            in the current (admin) language. E.g. a page is written in english
            but the admin language is set to Spanish, you will get a 'translate'
            button in stead of an 'edit' button (with the exact same action,
            though!)
        """
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        ## do not show when creating or updating
        if self.status in (Toolbar.UPDATE, Toolbar.CREATE):
            return False
        active_language = get_active_language()

        ## there's an instance, it has (primary) content but not in the
        ## active language
        if self.instance and self.instance.primary_content() and not \
           self.instance.content(language=active_language):
            return True
        return False

    def show_list(self):
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        if self.status == Toolbar.LIST:
            return False

        return True

    def show_view(self):
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        if self.status == Toolbar.VIEW:
            return False

        return True

    def show_attach(self):
        if self.status == Toolbar.SPECIAL:  ## special page
            return False

        if self.status == Toolbar.ATTACH:
            return False

        if self.instance and self.instance.primary_content():
            return False
        return bool(self.instance)

    def show_settings(self):
        ## XXX decent permissions
        user = self.request.user
        return access.has_access(user)

    def worklist(self):
        """ return list of items to be reviewed """
        pending = default_worklist()
        ## TODO: group by type?
        return dict(count=pending.count(), items=pending)

    def clipboard(self):
        """ return list of items in the clipboard """
        clipboard_copy = self.request.session.get('clipboard_copy', [])
        clipboard_cut = self.request.session.get('clipboard_cut', [])

        clipboard = clipboard_copy or clipboard_cut

        return dict(count=len(clipboard),
                    copy=bool(clipboard_copy),
                    cut=bool(clipboard_cut),
                    items=[Node.objects.get(tree_path=i).content() for i in clipboard])

    def translations(self):
        """
            Return data for the translations/languages menu. This means
            "switch to" options for translated languages and "translate to"
            for untranslated languages.

            If there's no second language (ignoring 'Any'), don't return
            anything; this will hide the translation menu entirely.
        """
        if not self.instance or self.status == Toolbar.SPECIAL:
            return None

        if len(settings.CONTENT_LANGUAGES) == 1:
            return None

        active = None
        translated = []
        untranslated = []

        active_language = get_active_language()

        for (lang, langtitle) in translate.languages():
            option = dict(id=lang, language=langtitle)
            content = self.instance.content(language=lang)

            ## In view mode toch edit tonen om vertaling te maken!
            base_url = "switch_admin_language?path=" + self.instance.tree_path + "&switchto=" + lang
            if lang == active_language:
                active = option
            else:
                if self.status == Toolbar.UPDATE:
                    option['action_url'] = base_url + '&rest=edit'
                elif self.status == Toolbar.VIEW:
                    option['action_url'] = base_url + ''
                elif self.status == Toolbar.LIST:
                    option['action_url'] = base_url + '&rest=list'
                elif self.status == Toolbar.CREATE:
                    option['action_url'] = base_url + '&rest=' + urllib2.quote('create?type=' + self.request.GET.get('type'))

                if content and self.status != Toolbar.CREATE:
                    translated.append(option)
                else:
                    untranslated.append(option)

        return dict(active=active,
                    translated=translated,
                    untranslated=untranslated)

    def button_actions(self):
        ## order?
        actions = []

        # import pdb; pdb.set_trace()
        
        for a in toolbar_registry.values() + self.actions:
            if a.type == "button":
                if not a.states or self.status in a.states:
                    actions.append(a.with_toolbar(self))

        return actions

    def username(self):
        """ attempt to return a reasonable username """
        user = self.request.user
        name = user.get_full_name().strip() or user.email
        if not name:
            name = user.username
        return name

from registries.toolbar import toolbar_registry
import copy

from django.template.loader import render_to_string
from django.template import RequestContext

class ToolbarAction(object):
    type = "generic"
    states = ()

    template = "wheelcms_axle/toolbar/action.html"

    def __init__(self, id, toolbar=None):
        self.id = id
        self.toolbar = toolbar

    def name(self):
        return 'unknown'

    def show(self):
        return self.toolbar and self.toolbar.instance

    def url(self):
        pass

    def with_toolbar(self, toolbar):
        a = copy.copy(self)
        a.toolbar = toolbar
        return a

    def render(self, context):
        return render_to_string(self.template, {"action":self},
                                context_instance=context)


class ButtonAction(ToolbarAction):
    type = "button"

    def icon(self):
        return None

class PreviewAction(ButtonAction):
    states = ('view',)

    def icon(self):
        return "eye-open"

    def attrs(self):
        return dict(target="_blank")

    def name(self):
        return 'Preview'

    def url(self):
        if self.show():
            return self.toolbar.instance.get_absolute_url() + \
                   "?select_layer=visitor"
