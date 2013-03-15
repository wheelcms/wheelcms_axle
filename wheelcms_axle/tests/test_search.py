from .models import Type1

from haystack.query import SearchQuerySet, EmptySearchQuerySet

class TestSearch(object):
    def test_1(self, client):
        t = Type1(title="hi").save()

        sqs = SearchQuerySet()
        res = sqs.auto_query("hi")
        assert res[0].object == t

        res = sqs.auto_query("frop")
        assert not res

