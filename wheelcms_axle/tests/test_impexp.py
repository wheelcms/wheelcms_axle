"""
    Test the various aspects/components of content serialization/deserialization
"""

from django.contrib.auth.models import User
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree

from ..impexp import WheelSerializer, Exporter, Importer
from ..node import Node

from .models import Type1, Type1Type, Type2, Type2Type

def p(n):
    print ElementTree.tostring(n, 'utf-8')

class TestExporter(object):
    """
        Verify it returns parsable xml,
        it handles errors as expected,
        it handles arguments (eg. path) as expected
        works recursive

        test order?
    """
    def test_xml(self, client):
        root = Node.root()
        content = Type1(node=root, state="published", title="Export Test").save()
        exporter = Exporter()
        xml, files = exporter.run(root)
        assert xml
        assert isinstance(xml, Element)
        assert xml.tag == 'site'
        assert xml.attrib.get('version', -1) == '1'
        assert xml.attrib.get('base', '--') == ''
        assert len(xml.getchildren()) == 1
        child = xml.getchildren()[0]
        assert child.tag == 'content'
        assert len(child.getchildren()) == 2
        children = child.find('children')
        assert len(children.getchildren()) == 0
        fields = child.find('fields')
        title = fields.find('field[@name="title"]')
        assert title.text == 'Export Test'

    def test_children(self, client):
        """ verify content is exported recursively """
        root = Node.root()
        Type1(node=root, state="published", title="Export Test").save()
        c1 = Type1(node=root.add("c1"), title="I'm c1").save()
        c2 = Type2(node=root.add("c2"), title="I'm c2").save()
        c1_1 = Type2(node=c1.node.add("c1_1"), title="I'm c1/c1_1").save()
        c2_1 = Type1(node=c2.node.add("c2_1"), title="I'm c2/c2_1").save()

        exporter = Exporter()
        xml, files = exporter.run(root)
        assert xml

        content = xml.findall('content') # one root node
        assert len(content) == 1
        root = content[0]
        root_children = root.findall('children')  # one children tag holding
        assert len(root_children) == 1
        root_children_content = root_children[0].findall('content')  # 2 childs
        assert len(root_children_content) == 2

        # import pytest; pytest.set_trace()
        c1 = root_children_content[0]
        assert c1.tag == "content"
        assert c1.attrib['slug'] == "c1"
        assert c1.attrib['type'] == Type1.get_name()

        c1_1 = c1.find("children").find("content")
        assert c1_1.tag == "content"
        assert c1_1.attrib['slug'] == "c1_1"
        assert c1_1.attrib['type'] == Type2.get_name()

        c2 = root_children_content[1]
        assert c2.tag == "content"
        assert c2.attrib['slug'] == "c2"
        assert c2.attrib['type'] == Type2.get_name()

        c2_1 = c2.find("children").find("content")
        assert c2_1.tag == "content"
        assert c2_1.attrib['slug'] == "c2_1"
        assert c2_1.attrib['type'] == Type1.get_name()


class TestImporter(object):
    """
        Verify it can parse xml and take action,
        it handles errors as expected,
        it handlers arguments (e.g. path, defaults, behaviour, version)
        as expected
        works recursive
        finds appropriate spoke
    """
    xml = """
<site base="" version="1">
 <content slug="" type="tests.type1">
  <fields>
   <field name="publication">2013-02-11T15:58:46.004222+00:00</field>
   <field name="created">2013-02-11T15:58:46.004279+00:00</field>
   <field name="meta_type">type1</field>
   <field name="title">Export Test</field>
   <field name="modified">2013-02-11T15:58:46.004275+00:00</field>
   <field name="state">published</field>
   <field name="expire">2033-02-14T15:58:46.004232+00:00</field>
   <field name="t1field">None</field>
   <field name="template" />
   <field name="owner" />
   <field name="navigation">False</field>
  </fields>
  <children>
   <content slug="c1" type="tests.type1">
    <fields>
     <field name="publication">2013-02-11T15:58:46.006591+00:00</field>
     <field name="created">2013-02-11T15:58:46.006646+00:00</field>
     <field name="meta_type">type1</field>
     <field name="title">I'm c1</field>
     <field name="modified">2013-02-11T15:58:46.006642+00:00</field>
     <field name="state">published</field>
     <field name="expire">2033-02-14T15:58:46.006600+00:00</field>
     <field name="t1field">None</field>
     <field name="template" />
     <field name="owner" />
     <field name="navigation">True</field>
    </fields>
    <children>
     <content slug="c1_1" type="tests.type2">
      <fields>
       <field name="publication">2013-02-11T15:58:46.012434+00:00</field>
       <field name="created">2013-02-11T15:58:46.012483+00:00</field>
       <field name="meta_type">type2</field>
       <field name="title">I'm c1/c1_1</field>
       <field name="modified">2013-02-11T15:58:46.012478+00:00</field>
       <field name="state">private</field>
       <field name="expire">2033-02-14T15:58:46.012443+00:00</field>
       <field name="template" />
       <field name="owner" />
       <field name="navigation">False</field>
      </fields>
      <children />
     </content>
    </children>
   </content>
  </children>
 </content>
</site>"""
    def test_recursive(self, client):
        """ import a recursive structure with different types """
        importer = Importer()
        # import pytest; pytest.set_trace()
        tree = ElementTree.fromstring(self.xml)
        res = importer.run(Node.root(), tree)

        root = Node.root()
        root_content = root.content()
        assert root_content.meta_type == Type1.__name__.lower()
        assert len(root.children()) == 1
        assert root.children()[0].path == "/c1"
        assert root_content.title == "Export Test"


        child0 = root.children()[0]
        child0_content = child0.content()

        assert len(child0.children()) == 1
        assert child0.path == "/c1"
        assert child0_content.title == "I'm c1"
        assert child0_content.navigation
        assert child0_content.state == "published"

        child0_0 = child0.children()[0]
        child0_0_content = child0_0.content()

        assert len(child0_0.children()) == 0
        assert child0_0.path == "/c1/c1_1"
        assert child0_0_content.title == "I'm c1/c1_1"
        assert not child0_0_content.navigation
        assert child0_0_content.state == "private"


class TestSerializer(object):
    """
        Serialization of default fields, custom field methods
    """
    def test_base(self, client):
        """ test the base content fields """
        t = Type1(state="published", title="Test", navigation=True).save()
        tt = Type1Type(t)
        s = WheelSerializer()
        res, file = s.serialize(tt)
        assert isinstance(res, Element)
        assert res.tag == "fields"
        assert len(res.getchildren())
        # import pytest; pytest.set_trace()
        assert res.find("field[@name='title']").text == "Test"
        assert res.find("field[@name='state']").text == "published"
        assert res.find("field[@name='publication']").text
        assert res.find("field[@name='created']").text
        assert res.find("field[@name='modified']").text
        assert res.find("field[@name='expire']").text
        assert res.find("field[@name='navigation']").text == "True"
        assert res.find("field[@name='meta_type']").text == tt.model.__name__.lower()
        assert not res.find("field[@name='owner']")
        assert not res.find("field[@name='node']")

    def test_owner(self, client):
        """ owners are exported to their usernames """
        owner = User.objects.get_or_create(username="johndoe")[0]
        tt = Type1Type(Type1(owner=owner).save())
        res, files = WheelSerializer().serialize(tt)
        assert res.find("field[@name='owner']").text == "johndoe"


class BaseSpokeImportExportTest(object):
    """
        Base test for any spoke that uses the default
        serialization or implements (extends) its own.
    """
    type = None
    spoke = None

    def create(self, **kw):
        t = self.type(**kw).save()
        tt = self.spoke(t)
        return tt

    def test_capable_serialize(self, client):
        """ verify the spoke is able to serialize itself """
        tt = self.create(state="published", title="Test", navigation=True)
        s = tt.serializer()
        res, files = s.serialize(tt)
        assert isinstance(res, Element)

    def test_capable_deserialize(self, client):
        """ verify the spoke is able to deserialize itself """
        ## step 0: create user / owner
        owner = User.objects.get_or_create(username="johndoe")[0]
        ## step 1: build XML
        tt = self.create(state="published", title="Hello World", navigation=True, owner=owner)
        s = tt.serializer()
        res, files = s.serialize(tt)

        ## step 2: deserialize it
        tt = self.spoke.serializer().deserialize(self.spoke, res)
        assert isinstance(tt, self.spoke)
        assert tt.instance.title == "Hello World"
        assert tt.instance.state == "published"
        assert tt.instance.navigation
        assert tt.instance.owner == owner

    ## how about Image/File base types?

class TestType1BaseImportExport(BaseSpokeImportExportTest):
    type = Type1
    spoke = Type1Type

