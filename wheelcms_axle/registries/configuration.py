from wheelcms_axle.registry import Registry

class ConfigurationRegistry(dict):
    def register(self, *args):
        from ..configuration import BaseConfigurationHandler

        if len(args) == 1:
            # new style class
            klass = args[0]
        else:
            # old style key/label/model/form args
            _related, _label, _model, _form = args
            class klass(BaseConfigurationHandler):
                id = _related
                label = _label
                model = _model
                form = _form

        self[klass.id] = klass

    #def register(self, related, label, model, form):
    #    self[related] = (label, model, form)

configuration_registry = Registry(ConfigurationRegistry())
