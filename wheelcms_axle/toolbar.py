import urllib2

from wheelcms_axle.content import type_registry
from wheelcms_axle.node import Node
from wheelcms_axle.workflows.default import worklist as default_worklist
from wheelcms_axle import access
from wheelcms_axle.utils import get_active_language
from wheelcms_axle import translate


class Toolbar(object):
    """
        Wrap toolbar-related data, functionality

        Possible toolbar/context states:
        view - viewing content
        update - updating contetn
        list - listing content
        create - creating content
        special - not in a content-context
    """
    def __init__(self, instance, request, status="view"):
        self.instance = instance
        self.request = request
        self.status = status

    def type(self):
        if not (self.instance and self.instance.content()):
            return None

        return type_registry.get(self.instance.content().get_name())

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
            ch = type.addable_children()
            primary = type.primary

        return [dict(name=c.name(),
                     title=c.title,
                     icon_path=c.full_type_icon_path())
                for c in ch if c != primary]

    def show_create(self):
        if self.status == 'special':  ## special page
            return False

        ## do not show when creating or updating
        if self.status in ('create', 'update'):
            return False
        if self.type() is None:
            return True
        if self.type().children is None:
            return True
        return bool(self.type().children)

    def show_update(self):
        if self.status == 'special':  ## special page
            return False

        ## do not show when creating or updating
        if self.status in ("update", "create"):
            return False
        if not (self.instance and self.instance.content()):
            return False
        return True

    def show_translate(self):
        if self.status == 'special':  ## special page
            return False

        ## do not show when creating or updating
        if self.status in ("update", "create"):
            return False
        active_language = get_active_language(self.request)

        ## there's an instance, it has (primary) content but not in the
        ## active language
        if self.instance and self.instance.primary_content() and not self.instance.content(language=active_language):
            return True
        return False

    def show_list(self):
        if self.status == 'special':  ## special page
            return False

        if self.status == "list":
            return False

        return True

    def show_view(self):
        if self.status == 'special':  ## special page
            return False

        if self.status == "view":
            return False

        return True

    def show_attach(self):
        if self.status == 'special':  ## special page
            return False

        if self.status == "attach":
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
        if not self.instance or self.status == "special":
            return None

        active = None
        translated = []
        untranslated = []

        active_language = get_active_language(self.request)

        for (lang, langtitle) in translate.languages():
            option = dict(id=lang, language=langtitle)
            content = self.instance.content(language=lang)

            ## In view mode toch edit tonen om vertaling te maken!
            base_url = "switch_admin_language?path=" + self.instance.tree_path + "&language=" + lang
            if lang == active_language:
                active = option
            else:
                if self.status == "update":
                    option['action_url'] = base_url + '&rest=edit'
                elif self.status == "view":
                    option['action_url'] = base_url + ''
                elif self.status == "list":
                    option['action_url'] = base_url + '&rest=list'
                elif self.status == "create":
                    option['action_url'] = base_url + '&rest=' + urllib2.quote('create?type=' + self.request.GET.get('type'))

                if content and self.status != 'create':
                    translated.append(option)
                else:
                    untranslated.append(option)

        return dict(active=active,
                    translated=translated,
                    untranslated=untranslated)

