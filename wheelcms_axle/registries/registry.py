class Registry(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def set(self, wrapped):
        self.wrapped = wrapped

    def __iter__(self):
        return self.wrapped.__iter__()

    def __getattr__(self, name):
        return getattr(self.wrapped, name)
