import wrapt

class Registry(wrapt.ObjectProxy):
    def set(self, wrapped):
        self.__wrapped__ = wrapped

RegistryProxy = Registry
