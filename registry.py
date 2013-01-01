class Registry(dict):
    def register(self, o):
        self[o.name] = o

class SpokeRegistry(Registry):
    pass

spokes = SpokeRegistry()
register_spoke = spokes.register
