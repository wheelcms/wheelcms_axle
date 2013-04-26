from .registry import Registry

def action(f):
    """
        mark a method as being an action.
    """
    f.action = True
    return f

class ActionRegistry(dict):
    def register(self, action, path=None, spoke=None):
        pass

    def get(self, action, path=None, spoke=None):
        # ...
        ## give up if there's no explicit spoke context passed
        if not spoke:
            return None

        classhandler = getattr(spoke, action, None)
        if classhandler and getattr(classhandler, 'action', False):
            return classhandler
        return None

action_registry = Registry(ActionRegistry())
