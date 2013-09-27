"""
    Test the various aspects/components of content serialization/deserialization
"""

from django.contrib.auth.models import User
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree

from ..impexp import WheelSerializer, Exporter, Importer
from ..node import Node

from .models import Type1, Type1Type, Type2, Type2Type
from .models import TestFile, TestImage, TestFileType, TestImageType

from .test_spoke import filedata

def p(n):
    print ElementTree.tostring(n, 'utf-8')

def find_attribute(tree, tag, attribute, value):
    """
        python 2.6 elementree does not support complex path expressions

        http://stackoverflow.com/questions/13667979/python-2-6-1-expected-path-separator
    """
    for node in tree.findall(tag):
        if node.attrib.get(attribute) == value:
            return node
    return None

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
        content = Type1(node=root, state="published", title="Export Test", language="en").save()
        content.tags.add("xml")
        content.tags.add("export")

        exporter = Exporter()
        xml, files = exporter.run(root)
        assert xml
        assert xml.tag == 'site'
        assert xml.attrib.get('version', -1) == '1'
        assert xml.attrib.get('base', '--') == ''
        node = xml.find("node")
        assert node
        assert len(node.getchildren()) == 2

        children = node.find('children')
        assert len(children.getchildren()) == 0

        content = node.find("content")
        assert content
        assert content.tag == 'content'
        assert len(content.getchildren()) == 1

        fields = content.find('fields')
        title = find_attribute(fields, 'field', "name", "title")
        assert title.text == 'Export Test'

        tags = fields.findall("tags/tag")
        assert len(tags) == 2
        assert set((tags[0].text, tags[1].text)) == set(("xml", "export"))

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

        ## one root node
        nodes = [x for x in xml if x.tag == "node"]
        assert len(nodes) == 1
        root = nodes[0]

        ## containing a single content item
        contents = [x for x in root if x.tag == "content"]
        assert len(contents) == 1

        ## two child nodes
        root_children = root.find('children')
        assert root_children
        root_children_content = root_children.findall('node')  # 2 childs
        assert len(root_children_content) == 2

        c1node = root_children_content[0]
        c1 = c1node.find("content")
        assert c1.tag == "content"
        assert c1.attrib['slug'] == "c1"
        assert c1.attrib['type'] == Type1.get_name()

        c1_1node = c1node.find("children").find("node")
        c1_1 = c1_1node.find("content")
        assert c1_1.tag == "content"
        assert c1_1.attrib['slug'] == "c1_1"
        assert c1_1.attrib['type'] == Type2.get_name()

        c2node = root_children_content[1]
        c2 = c2node.find("content")
        assert c2.tag == "content"
        assert c2.attrib['slug'] == "c2"
        assert c2.attrib['type'] == Type2.get_name()

        c2_1node = c2node.find("children").find("node")
        c2_1 = c2_1node.find("content")
        assert c2_1.tag == "content"
        assert c2_1.attrib['slug'] == "c2_1"
        assert c2_1.attrib['type'] == Type1.get_name()

    def test_multilang(self, client):
        """ verify content is exported recursively """
        root = Node.root()
        Type1(node=root, state="published", title="EN Export Test", language="en").save()
        Type1(node=root, state="published", title="NL Export Test", language="nl").save()

        exporter = Exporter()
        xml, files = exporter.run(root)
        assert xml
        nodes = [x for x in xml if x.tag == "node"]
        assert len(nodes) == 1
        root = nodes[0]

        ## containing two translations
        contents = [x for x in root if x.tag == "content"]
        assert len(contents) == 2

        content_nl = [c for c in contents
                      if find_attribute(c.find("fields"),
                                        "field",
                                        "name", "language").text == "nl"][0]
        assert content_nl
        assert find_attribute(content_nl.find("fields"),
                 "field", "name", "title").text == "NL Export Test"

        content_en = [c for c in contents
                      if find_attribute(c.find("fields"),
                                        "field",
                                        "name", "language").text == "en"][0]
        assert content_en
        assert find_attribute(content_en.find("fields"),
                 "field", "name", "title").text == "EN Export Test"

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
 <node id="1" tree_path="">
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
     <tags>
       <tag>hello</tag>
       <tag>world</tag>
     </tags>
    </fields>
   </content>
   <children>
    <node id="2" tree_path="/2">
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
     </content>
     <children>
      <node id="3" tree_path="/2/3">
       <content slug="c1_1_en" type="tests.type2">
        <fields>
         <field name="language">en</field>
         <field name="publication">2013-02-11T15:58:46.012434+00:00</field>
         <field name="created">2013-02-11T15:58:46.012483+00:00</field>
         <field name="meta_type">type2</field>
         <field name="title">I'm c1/c1_1 EN</field>
         <field name="modified">2013-02-11T15:58:46.012478+00:00</field>
         <field name="state">private</field>
         <field name="expire">2033-02-14T15:58:46.012443+00:00</field>
         <field name="template" />
         <field name="owner" />
         <field name="navigation">False</field>
        </fields>
       </content>
       <content slug="c1_1_nl" type="tests.type2">
        <fields>
         <field name="language">nl</field>
         <field name="publication">2013-02-11T15:58:46.012434+00:00</field>
         <field name="created">2013-02-11T15:58:46.012483+00:00</field>
         <field name="meta_type">type2</field>
         <field name="title">I'm c1/c1_1 NL</field>
         <field name="modified">2013-02-11T15:58:46.012478+00:00</field>
         <field name="state">private</field>
         <field name="expire">2033-02-14T15:58:46.012443+00:00</field>
         <field name="template" />
         <field name="owner" />
         <field name="navigation">False</field>
        </fields>
       </content>
       <children />
      </node>
     </children>
    </node>
   </children>
 </node>
</site>"""
    def test_recursive(self, client):
        """ import a recursive structure with different types """
        importer = Importer()
        # import pytest; pytest.set_trace()
        tree = ElementTree.fromstring(self.xml)
        res = importer.run(tree)

        root = Node.root()
        root_content = root.content()
        assert root_content.meta_type == Type1.__name__.lower()
        assert len(root.children()) == 1
        assert root.children()[0].path == "/c1"
        assert root_content.title == "Export Test"

        assert set(root_content.tags.values_list("name", flat=True)) == set(("hello", "world"))


        child0 = root.children()[0]
        child0_content = child0.content()

        assert len(child0.children()) == 1
        # import pytest; pytest.set_trace()
        child0_0_nl = child0.child("c1_1_nl", language="nl")
        child0_0_en = child0.child("c1_1_en", language="en")


        assert child0.path == "/c1"
        assert child0_content.title == "I'm c1"
        assert child0_content.navigation
        assert child0_content.state == "published"

        child0_0_nl_content = child0_0_nl.content()

        assert len(child0_0_nl.children()) == 0
        assert child0_0_nl.path == "/c1/c1_1_nl"
        assert child0_0_nl_content.title == "I'm c1/c1_1 NL"
        assert not child0_0_nl_content.navigation
        assert child0_0_nl_content.state == "private"

        child0_0_en_content = child0_0_en.content()

        assert len(child0_0_en.children()) == 0
        assert child0_0_en.path == "/c1/c1_1_en"
        assert child0_0_en_content.title == "I'm c1/c1_1 EN"
        assert not child0_0_en_content.navigation
        assert child0_0_en_content.state == "private"

    def test_base(self, client):
        """ import a recursive structure with different types """
        subsub = Node.root().add("sub1").add("sub2")

        importer = Importer(subsub)
        tree = ElementTree.fromstring(self.xml)
        res = importer.run(tree)

        assert len(Node.root().children()) == 1
        assert subsub.content().meta_type == Type1.__name__.lower()
        assert len(subsub.children()) == 1
        assert subsub.children()[0].path == "/sub1/sub2/c1"
        assert subsub.content().title == "Export Test"


class TestDelay(object):
    class DelaySerializer(WheelSerializer):
        extra = ('test', )

        def deserialize_extra_test(self, extra, tree, model):
            def delay():
                return 42
            return delay

    def test_delay(self, client):
        # import pytest; pytest.set_trace()
        tree = ElementTree.fromstring('<content type="tests.type1" slug="/a1"></content>')
        t, delay = TestDelay.DelaySerializer().deserialize(Type1Type, tree)
        assert len(delay)
        assert delay[0]() == 42


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
        assert res.tag == "fields"
        assert len(res.getchildren())
        assert find_attribute(res, "field", "name", 'title').text == "Test"
        assert find_attribute(res, "field", "name", 'state').text == "published"
        assert find_attribute(res, "field", "name", 'publication').text
        assert find_attribute(res, "field", "name", 'created').text
        assert find_attribute(res, "field", "name", 'modified').text
        assert find_attribute(res, "field", "name", 'expire').text
        assert find_attribute(res, "field", "name", 'navigation').text == "True"
        assert find_attribute(res, "field", "name", 'meta_type').text == tt.model.__name__.lower()
        assert not find_attribute(res, "field", "name", 'owner')
        assert not find_attribute(res, "field", "name", 'node')

    def test_owner(self, client):
        """ owners are exported to their usernames """
        owner = User.objects.get_or_create(username="johndoe")[0]
        tt = Type1Type(Type1(owner=owner).save())
        res, files = WheelSerializer().serialize(tt)
        assert find_attribute(res, "field", "name", 'owner').text == "johndoe"

from wheelcms_axle.models import Configuration
from wheelcms_axle.tests.models import Configuration as ConfigurationTest

class TestConfigImportExport(object):
    """ configuration import/export tests """

    def test_export(self, client):
        """ Test export of main and sub config """
        c = Configuration.config()
        c.title = "Test Site"
        c.description = "Test Description"
        c.save()

        t = ConfigurationTest(main=c, value="conftest")
        t.save()

        root = Node.root()
        exporter = Exporter()
        xml, files = exporter.run(root)
        assert xml

        main = find_attribute(xml, "config", "set", "")
        testconf = find_attribute(xml, "config", "set", "testconf")

        assert main
        assert testconf

        assert find_attribute(main, "item", "name", "title").text == "Test Site"
        assert find_attribute(testconf, "item", "name", "value").text == "conftest"

    def test_import(self, client):
        """ test import of main and sub config """
        xml = """<site base="" version="1"><node id="1" tree_path=""><children /></node><config set=""><item name="id">1</item><item name="title">Test Site</item><item name="description">Test Description</item><item name="theme">default</item><item name="analytics" /><item name="head" /><item name="sender" /><item name="sendermail" /><item name="mailto" /></config><config set="testconf"><item name="value">conftest</item></config></site>"""

        root = Node.root()

        importer = Importer(root)
        tree = ElementTree.fromstring(xml)
        res = importer.run(tree)

        c = Configuration.config()
        assert c.title == "Test Site"
        assert c.description == "Test Description"
        assert c.testconf.all()[0].value == "conftest"


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
        assert res.tag == "fields"

    def test_capable_deserialize(self, client):
        """ verify the spoke is able to deserialize itself """
        ## step 0: create user / owner
        owner = User.objects.get_or_create(username="johndoe")[0]
        ## step 1: build XML
        tt = self.create(state="published", title="Hello World", navigation=True, owner=owner)
        s = tt.serializer()
        res, files = s.serialize(tt)

        ## step 2: deserialize it
        tt, delay = self.spoke.serializer().deserialize(self.spoke, res)
        assert tt.instance.title == "Hello World"
        assert tt.instance.state == "published"
        assert tt.instance.navigation
        assert tt.instance.owner == owner

    ## how about Image/File base types?

class TestType1ImportExport(BaseSpokeImportExportTest):
    type = Type1
    spoke = Type1Type

class TestFileImportExport(BaseSpokeImportExportTest):
    type = TestFile
    spoke = TestFileType

    def test_file_serialize(self, client):
        tt = self.create(state="published", title="Hello", storage=filedata)
        s = tt.serializer()
        res, files = s.serialize(tt)
        assert files
        assert "files/foo.png" in files

class TestImageImportExport(BaseSpokeImportExportTest):
    type = TestImage
    spoke = TestImageType

    def test_image_serialize(self, client):
        tt = self.create(state="published", title="Hello", storage=filedata)
        s = tt.serializer()
        res, files = s.serialize(tt)
        assert files
        assert "images/foo.png" in files
