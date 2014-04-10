import mock
from json import loads
from taggit.models import Tag

from ..spoke import Spoke
from ..forms import TagWidget


class TestTagAction(object):
    """ Test the Tag action on Spoke, responsible for finding
        autocomplete tags """
    def test_empty(self, client):
        s = Spoke(mock.MagicMock())
        handler = mock.MagicMock()
        request = mock.MagicMock(GET={})

        res = s.tags(handler, request, "tags")
        assert loads(res.content) == []

    def test_empty_query(self, client):
        """ Empty query """
        Tag(name="t1").save()
        Tag(name="t2").save()

        s = Spoke(mock.MagicMock())
        handler = mock.MagicMock()
        request = mock.MagicMock(GET={})

        res = s.tags(handler, request, "tags")
        assert set(loads(res.content)) == set(("t1", "t2"))

    def test_startmatch(self, client):
        """ single match on string start """
        Tag(name="abcdef").save()
        Tag(name="cdefghab").save()

        s = Spoke(mock.MagicMock())
        handler = mock.MagicMock()
        request = mock.MagicMock(GET={"query":"ab"})

        res = s.tags(handler, request, "tags")
        assert loads(res.content) == ["abcdef"]

    def test_startmatch_case(self, client):
        """ multiple matches, different casing """
        Tag(name="abCDef").save()
        Tag(name="abcdef").save()

        s = Spoke(mock.MagicMock())
        handler = mock.MagicMock()
        request = mock.MagicMock(GET={"query":"ab"})

        res = s.tags(handler, request, "tags")
        assert set(loads(res.content)) == set(("abcdef", "abCDef"))


class TestTagWidget(object):
    """ Test some of the specific behaviour in the TagWidget """

    def test_nonevalue(self):
        """ value can be None """
        tw = TagWidget()
        res = tw.render("tags", None, attrs={'foo':'bar'})
        assert 'value=""' in res

    def test_stringvalue(self):
        """ It can be passed a string value """
        tw = TagWidget()
        res = tw.render("tags", "a,b,c", attrs={'foo':'bar'})
        assert res.startswith("<inputwrap ")
        assert res.endswith("inputwrap>")
        assert 'value="a,b,c"' in res

    def test_instancevalue(self):
        """ Or an instance in which case its tags should be resolved """
        tw = TagWidget()

        def mock_sr(_):
            return [mock.MagicMock(**{"tag.name":"this"}),
                    mock.MagicMock(**{"tag.name":"that"})]

        mockvalue = mock.MagicMock(select_related=mock_sr)

        res = tw.render("tags", mockvalue, attrs={'foo':'bar'})
        assert res.startswith("<inputwrap ")
        assert res.endswith("inputwrap>")
        assert 'value="this,that"' in res
