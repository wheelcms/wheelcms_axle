class DummyContent(object):
    meta_type = 'dummycontent'

    def __init__(self, allowed=None):
        self.allowed = allowed

    @classmethod
    def get_name(cls):
        return "test." + cls.meta_type

class MockedQueryDict(dict):
    def getlist(self, k):
        return self.get(k)

