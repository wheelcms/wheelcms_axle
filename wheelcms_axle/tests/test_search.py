from .models import Type1Type, Type2Type
from wheelcms_axle.content import TypeRegistry, type_registry
from wheelcms_axle.node import Node
from wheelcms_axle.spoke import indexfactory

from haystack.query import SearchQuerySet, EmptySearchQuerySet
from haystack import site

class BaseTestSearch(object):
    type = None
    other = Type1Type

    def construct_type(self, **kw):
        """ allow construction to be overridden for more complex types """
        return self.type.model(**kw).save()

    def construct_other(self, **kw):
        """ 'other' is a type unequal to 'type', to test against """
        return self.other.model(**kw).save()

    def setup(self):
        site._registry = {}

        self.registry = TypeRegistry()
        type_registry.set(self.registry)
        self.registry.register(self.type)
        self.registry.register(self.other)
        self.sqs = SearchQuerySet()

    def test_trivial_match(self, client):
        t = self.construct_type(title="hi")

        res = self.sqs.auto_query("hi")
        assert res[0].object == t

    def test_trivial_nonmatch(self, client):
        t = self.construct_type(title="hi")

        res = self.sqs.auto_query("frop")
        assert not res

    def test_find_metatype(self, client):
        """ should become a spoke-related match """
        t = self.construct_type(title="hi")
        o = self.construct_other(title="hi")

        res = self.sqs.filter(content="hi", type=self.type.model.classname)
        assert len(res) == 1   ## not 2!
        assert res[0].object == t

    def test_find_metaother(self, client):
        """ should become a spoke-related match """
        t = self.construct_type(title="hi")
        o = self.construct_other(title="hi")

        res = self.sqs.filter(content="hi", type=self.other.model.classname)
        assert len(res) == 1   ## not 2!
        assert res[0].object == o

    def test_workflow_state(self, client):
        t1 = self.construct_type(title="hi", state="private")
        t2 = self.construct_type(title="hi", state="published")

        res = self.sqs.filter(state="published")
        assert len(res) == 1
        assert res[0].object == t2

    def xtest_path(self, client):
        """ One of the few node attributes to be indexed """
        ## Test won't work on simple backend
        root = Node.root()
        c1 = root.add("child1")
        c2 = c1.add("child2")
        t1 = self.construct_type(title="hi", node=c2)
        t2 = self.construct_type(title="hi", node=c1)

        res = self.sqs.filter(content="hi", path="/child1/child2")
        assert len(res) == 1
        assert res[0].object == t1

    def xtest_slug(self, client):
        ## Test won't work on simple backend
        root = Node.root()
        c1 = root.add("child1")
        c2 = c1.add("child2")
        t1 = self.construct_type(title="hi", node=c2)
        t2 = self.construct_type(title="hi", node=c1)

        res = self.sqs.filter(content="hi", slug="child2")
        assert len(res) == 1
        assert res[0].object == t1

    def test_searchable(self, client):
        t1 = self.construct_type(title="hello world")
        t2 = self.construct_type(description="hello world")

        res = self.sqs.filter(content="hello")
        assert len(res) == 2
        assert res[0].object in (t1, t2)
        assert res[1].object in (t1, t2)

    def test_indexfactory(self, client):
        root = Node.root()
        c1 = root.add("child1")
        c2 = c1.add("child2")
        t1 = self.construct_type(title="hi", state="private", node=c2)
        idf = indexfactory(self.type)
        idx = idf(self.type.model)
        data = idx.prepare(t1)

        assert data['title'] == 'hi'
        assert data['state'] == 'private'
        assert data['path'] == c2.get_absolute_url()

class TestSearch(BaseTestSearch):
    type = Type1Type
    other = Type2Type

