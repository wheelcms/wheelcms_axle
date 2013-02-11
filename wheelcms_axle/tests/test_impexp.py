"""
    Test the various aspects/components of content serialization/deserialization
"""

from django.contrib.auth.models import User
from xml.etree.ElementTree import Element, SubElement, tostring, tostring

from ..impexp import WheelSerializer, Exporter, Importer
from ..node import Node

from .models import Type1, Type1Type

def p(n):
    print tostring(n, 'utf-8')

class TestExporter(object):
    """
        Verify it returns parsable xml,
        it handles errors as expected,
        it handles arguments (eg. path) as
        expected
    """
    def test_xml(self, client):
        root = Node.root()
        content = Type1(node=root, state="published", title="Export Test").save()
        exporter = Exporter()
        res = exporter.run(root)
        assert res
        assert isinstance(res, Element)
        assert res.tag == 'site'
        assert res.attrib.get('version', -1) == '1'
        assert res.attrib.get('base', '--') == ''
        assert len(res.getchildren()) == 1
        child = res.getchildren()[0]
        assert child.tag == 'content'
        assert len(child.getchildren()) == 2
        children = child.find('children')
        assert len(children.getchildren()) == 0
        fields = child.find('fields')
        title = fields.find('title')
        assert title.text == 'Export Test'


class TestImporter(object):
    """
        Verify it can parse xml and take action,
        it handles errors as expected,
        it handlers arguments (e.g. path, defaults, behaviour, version)
        as expected
    """


class TestSerializer(object):
    """
        Serialization of default fields, custom field methods
    """
    def test_base(self, client):
        """ test the base content fields """
        t = Type1(state="published", title="Test", navigation=True).save()
        tt = Type1Type(t)
        s = WheelSerializer()
        res = s.serialize(tt)
        assert isinstance(res, Element)
        assert res.tag == "fields"
        assert len(res.getchildren())
        assert res.find("title").text == "Test"
        assert res.find("state").text == "published"
        assert res.find("publication").text
        assert res.find("created").text
        assert res.find("modified").text
        assert res.find("expire").text
        assert res.find("navigation").text == "True"
        assert res.find("meta_type").text == tt.model.get_name()
        assert not res.find("owner")
        assert not res.find('node')

    def test_owner(self, client):
        """ owners are exported to their usernames """
        owner = User.objects.get_or_create(username="johndoe")[0]
        tt = Type1Type(Type1(owner=owner).save())
        res = WheelSerializer().serialize(tt)
        assert res.find("owner").text == "johndoe"


class BaseSpokeImportExportTest(object):
    """
        Base test for any spoke that uses the default
        serialization or implements (extends) its own.
    """
    def test_capable_serialize(self, client):
        """ verify the spoke is able to serialize itself """
        pass

    def test_capable_deserialize(self, client):
        """ verify the spoke is able to deserialize itself """
        pass
    ## how about Image/File base types?
