from wheelcms_axle.models import type_registry

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
    def __init__(self, instance, status="view"):
        self.instance = instance
        self.status = status

    def type(self):
        if not (self.instance and self.instance.content()):
            return None

        return type_registry.get(self.instance.content().meta_type)

    def children(self):
        type = self.type()
        ## order?
        ## unconnected, or no restrictions
        if type is None:
            ch = type_registry.values()
        else:
            ch = type.addable_children()

        return [dict(name=c.name()) for c in ch]

    def show_create(self):
        if self.status == 'special':  ## special page
            return False

        if self.status == 'create':
            return False
        if self.type() is None:
            return True
        if self.type().children is None:
            return True
        return bool(self.type().children)

    def show_update(self):
        if self.status == 'special':  ## special page
            return False

        if self.status == "update":
            return False
        if not self.instance or self.instance.content():
            return False
        return True

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

        if not self.instance or self.instance.content():
            return False
        return True

