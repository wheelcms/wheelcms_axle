from .registry import Registry
from drole.types import Permission

def action(f):
    """
        mark a method as being an action.
    """
    if isinstance(f, Permission):
        def decorator(decorated):
            decorated.action = True
            decorated.permission = f
            return decorated
        return decorator
    else:
        f.action = True
        f.permission = None
    return f

class ActionRegistry(dict):
    def register(self, handler, action, path=None, spoke=None):
        if action not in self:
            self[action] = []
        self[action].append((handler, path, spoke))

    def get(self, action, path=None, spoke=None):
        """
            Action resolution is as follows:
            - A handler is registered on an action and optionally a spoke and
              path
            - spoke and path have to match if specified
            if there are no entries at all, find a handler on the spoke
            itself.

            To consider: add priority when registering action

            Een action / handler registreer je in een bepaalde context:
            - globaal (geld in iedere context)
            - voor bepaalde spoke
            - voor bepaald path
            - spoke en path

            Vervolgens zoek je een handler in die context. Als je een nauwkeurige
            context specificeert, dan verwacht

            Een action die op path P en spoke S geregistreerd is matcht dus
            niet op path P' en spoke S
        """
        entries = super(ActionRegistry, self).get(action)

        if entries:
            ## Match spoke against an actual instance first
            for (h, epath, espoke) in entries:
                if epath and path != epath:
                    continue
                if espoke and spoke != espoke:
                    continue
                return h
            ## and then against a spoke type class
            for (h, epath, espoke) in entries:
                if epath and path != epath:
                    continue
                if espoke and espoke != spoke.__class__:
                    continue
                return h

        ## give up if there's no explicit spoke context passed
        if not spoke:
            return None

        classhandler = getattr(spoke, action, None)
        if classhandler and getattr(classhandler, 'action', False):
            return classhandler
        return None

class tab(object):
    def __init__(self, permission=None, id=None, label=None, condition=None):
        self.permission = permission
        self.id = id
        self.label = label
        self.condition = condition

    def __call__(self, f):
        def wrapped(self, *a, **b):
            res = f(self, *a, **b)
            return res

        name = f.func_name

        if self.permission:
            wrapped = action(self.permission)(wrapped)
        else:
            wrapped = action(wrapped)
        wrapped.tab = True
        wrapped.tab_id = self.id or name
        wrapped.tab_label = self.label or wrapped.tab_id
        wrapped.condition = self.condition

        return wrapped

def tabaction(handler):
    """ return the tab identifier of a handler if it's a tab, or else None """
    if getattr(handler, 'action', False) and getattr(handler, 'tab', False):    
        return handler.tab_id
    return None

action_registry = Registry(ActionRegistry())
