from wheelcms_axle.registries.registry import Registry
from UserDict import IterableUserDict

class WorkflowRegistry(IterableUserDict):
    _default = None

    def get_default(self):
        return self._default

    def set_default(self, workflow):
        self._default = workflow

    def register(self, spoke, workflow):
        self[spoke] = workflow

    def get(self, spoke, default=None):
        return IterableUserDict.get(self, spoke, default) or self.get_default()

    def __getitem__(self, spoke):
        try:
            return IterableUserDict.__getitem__(self, spoke)
        except KeyError:
            return self._default
