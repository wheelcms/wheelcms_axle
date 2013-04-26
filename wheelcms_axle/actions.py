from .registry import Registry

def action(f):
    """
        mark a method as being an action.
    """
    f.action = True
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
            for (h, epath, espoke) in entries:
                if epath and path != epath:
                    continue
                if espoke and spoke != espoke:
                    continue
                return h

        ## give up if there's no explicit spoke context passed
        if not spoke:
            return None

        classhandler = getattr(spoke, action, None)
        if classhandler and getattr(classhandler, 'action', False):
            return classhandler
        return None

action_registry = Registry(ActionRegistry())
