"""
    Import / Export of content

    Requirements:

    - exporting of new types should work, but can be customized
    - xml definitions are versioned, backwards compatibility should be
      present

    - should position be exported? Or should xml order be used, and position
      be renumbered when importing?

    - due to the current nature of nodes, content with a path of /foo/bar may
      exist without a node named /foo. This is an inconsistency in the node tree.
      Such an implementation detail is not relevant to the import/export, 
      but how can we handle content without a strict parent? Make it unattached?

    - how to export nodes without content? (unattached nodes)

    - how to handle related content? This can be a User object (its id can 
      change) or entirely new models (custom export?)


    Structure (roughly)
    <site version="1" ..>
      <content type=".." slug="..." position="1">
        <created></created>
        <publication></publication>
        <expires></expires>
        <title></title>

        <children>
          <content type=".." slug="..">
          </content>
        </children>
      </content>
      <unattached>

      </unattached>
    </site>
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from django.utils.encoding import smart_unicode

class WheelSerializer(object):
    """ (de) serialize wheel content """
    skip = ('node', )

    def __init__(self):
        pass

    def serialize_owner(self, field, o):
        # import pytest; pytest.set_trace()
        value = getattr(o, field.name, None)
        # value = smart_unicode(value)
        if value is None:
            return ""
        return smart_unicode(value.username)

    def serialize(self, spoke):
        o = spoke.instance
        fields = {}
        for field in o._meta.concrete_model._meta.fields:
            handler = getattr(self, "serialize_%s" % field.name, None)
            if field.name in self.skip:
                continue

            if handler:
                fields[field.name] = handler(field, o)
            elif field.serialize:
                if field.rel is None:
                    value = field.value_to_string(o)
                else:
                    value = getattr(o, field.get_attname())
                    value = smart_unicode(value)

                fields[field.name] = value
        xmlfields = Element("fields")
        for k, v in fields.iteritems():
            e = SubElement(xmlfields, k)
            e.text = v
        return xmlfields


    def deserialize(self, xml):
        pass


class Exporter(object):
    VERSION = 1

    def __init__(self, verbose=0):
        self.verbose = verbose

    def export_node(self, parent, node):
        # import pdb; pdb.set_trace()
        
        try:
            spoke = node.content().spoke()
        except AttributeError:
            spoke = None

        xmlcontent = SubElement(parent, "content", dict(slug=node.slug()))
        if spoke:
            contentxml = spoke.serializer().serialize(spoke)
            xmlcontent.append(contentxml)

        children = SubElement(xmlcontent, "children")
        for child in node.children():
            self.export_node(children, child)

    def run(self, node, base="", unattached=True, attachinline=True):
        """ export node and all content beneath it. If unattached is True,
            also export unattached content.
            
            attachments can be inline or exported to a folder
        """
        root = Element("site")
        root.set('version', str(self.VERSION))
        root.set('base', base)
        self.export_node(root, node)
        return root

class Importer(object):
    pass
