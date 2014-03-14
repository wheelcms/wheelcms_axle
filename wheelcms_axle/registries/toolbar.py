from wheelcms_axle.registry import Registry

class ToolbarActionRegistry(dict):
    def register(self, action):
        self[action.id] = action

## toolbar_registry = registries.register('toolbar', ConfigurationRegistry)

toolbar_registry = Registry(ToolbarActionRegistry())
