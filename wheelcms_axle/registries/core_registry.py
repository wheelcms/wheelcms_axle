from .registry import RegistryProxy

##
## Idea: A stack of registries, the topone being the one consulted.
## This allows a test to push/pop newly initialized registries, same for custom
## setups. Optionally name levels (e.g. toplevel == global). Might even 
## search across levels

class CoreRegistry(object):
    def __init__(self):
        self.__dict__['reg'] = {} ## bypass __setattr__ recursion

    def set(self, name, registry):
        wrapped = RegistryProxy(registry)
        self.reg[name] = wrapped
        return wrapped

    def __getattr__(self, k):
        try:
            return self.reg[k]
        except KeyError:
            raise AttributeError(k)

    def __setattr__(self, k, v):
        self.set(k, v)

core = CoreRegistry()
