from wheelcms_axle.models import type_registry

class Toolbar(object):
    """
        Wrap toolbar-related data, functionality
    """
    def __init__(self, instance, status="view"):
        self.instance = instance
        self.status = status

    def type(self):
        if not self.instance.content():
            return None

        return type_registry.get(self.instance.content().meta_type)

    def children(self):
        type = self.type()
        ## order?
        ## unconnected, or no restrictions
        if type is None or type.children is None:
            ch = type_registry.values()
        else:
            ch = type.children

        return [dict(name=c.name()) for c in ch]

    def show_create(self):
        if self.status == 'create':
            return False
        if self.type() is None:
            return True
        if self.type().children is None:
            return True
        return bool(self.type().children)
