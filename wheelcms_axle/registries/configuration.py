from wheelcms_axle.registry import Registry

class ConfigurationRegistry(dict):
    def register(self, related, label, model, form):
        self[related] = (label, model, form)

configuration_registry = Registry(ConfigurationRegistry())
