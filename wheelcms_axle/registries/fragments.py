from wheelcms_axle.registry import Registry

class FragmentsRegistry(dict):
    def register(self, name, template, priority=100):
        if name not in self:
            self[name] = []
        self[name].append((priority, template))

fragments_registry = Registry(FragmentsRegistry())
