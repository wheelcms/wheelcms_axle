
class MockedQueryDict(dict):
    def getlist(self, k):
        return self.get(k)

