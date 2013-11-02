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

    Should a field be serialized to <title> or <field name="title">? The
    former will not allow for a schema definition
"""
import os

from xml.etree.ElementTree import Element, SubElement, tostring
from django.utils.encoding import smart_unicode
from django.contrib.auth.models import User
from django.db.models import FileField

from .content import type_registry
from .node import Node
from .registries.configuration import configuration_registry


class SerializationException(Exception):
    pass


class WheelSerializer(object):
    """ (de) serialize wheel content """
    skip = ('node', )
    extra = ('tags', )

    def __init__(self, basenode=None, update_lm=True):
        self.basenode = basenode or Node.root()
        self.update_lm = update_lm


    def serialize_owner(self, field, o):
        # import pytest; pytest.set_trace()
        value = getattr(o, field.name, None)
        # value = smart_unicode(value)
        if value is None:
            return ""
        return smart_unicode(value.username)

    def deserialize_owner(self, field, tree):
        username = tree.text
        if not username:
            return None
        return User.objects.get(username=username)

    def serialize_extra_tags(self, field, o):
        tags = list(o.tags.values_list("name", flat=True))
        res = []
        for t in tags:
            res.append(dict(name="tag", value=t))
        return dict(name="tags", value=res)

    def deserialize_extra_tags(self, extra, tree, model):
        tags = []
        for tag in tree.findall("tags/tag"):
            tags.append(tag.text)
        model.tags.add(*tags)

    def serialize(self, spoke):
        o = spoke.instance

        files = []

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
                if isinstance(field, FileField):
                    files.append(value)

        for e in self.extra:
            handler = getattr(self, "serialize_extra_%s" % e, None)
            if handler:
                fields[e] = handler(e, o)

        ## tags arent fields but a manager, handle
        ## separately
        xmlfields = Element("fields")

        for k, v in fields.iteritems():
            if isinstance(v, dict):
                tag = v['name']
                value = v['value']
                e = SubElement(xmlfields, tag)
                try:
                    for vv in value:
                        SubElement(e, vv['name']).text = vv['value']
                except TypeError: # not a sequence
                    e.text = value
            else:
                e = SubElement(xmlfields, "field")
                e.attrib['name'] = k
                e.text = v
        return xmlfields, files


    def deserialize(self, spoke, tree):
        model = spoke.model
        fields = {}
        # import pytest; pytest.set_trace()
        for field_node in tree.findall("field"):
            field_name = field_node.attrib.get("name")
            if not field_name:
                raise SerializationException("Missing name attribute")

            field = model._meta.get_field(field_name)

            handler = getattr(self, "deserialize_%s" % field.name, None)
            if handler:
                fields[field_name] = handler(field, field_node)

            ##elif field.rel and isinstance(field.rel, models.ManyToManyRel):
            ##    m2m_data[field.name] = self._handle_m2m_field_node(field_node, field)
            ##elif field.rel and isinstance(field.rel, models.ManyToOneRel):
            ##    data[field.attname] = self._handle_fk_field_node(field_node, field)
            else:
                value = field.to_python(field_node.text)
                ##
                ## In stead of setting a null value on a field that doesn't
                ## accept it, simply skip the field and let the default handle
                ## the value
                if value is not None or field.null:
                    fields[field_name] = value

        m = model(**fields).save(update_lm=self.update_lm)
        delays = []

        for e in self.extra:
            handler = getattr(self, "deserialize_extra_%s" % e, None)
            if handler:
                delay = handler(e, tree, m)
                if delay:
                    delays.append(delay)

        return spoke(m), delays


class Exporter(object):
    VERSION = 1

    def __init__(self, verbose=0):
        self.verbose = verbose

    def export_node(self, parent, node):
        # import pdb; pdb.set_trace()
        files = []


        nodetag = SubElement(parent, "node",
                             dict(id=str(node.pk), tree_path=node.tree_path))

        for content in node.contentbase.all():
            ## transform the baseclass into the actual instance
            content = content.content()

            spoke = content.spoke()
            type = spoke.model.get_name()

            xmlcontent = SubElement(nodetag, "content",
                                    dict(slug=node.slug(content.language),
                                    type=type))
            contentxml, files = spoke.serializer().serialize(spoke)
            xmlcontent.append(contentxml)

        children = SubElement(nodetag, "children")
        for child in node.children():
            files += self.export_node(children, child)

        return files

    def run(self, node, base="", unattached=True):
        """ export node and all content beneath it.
            If unattached is True,
            also export unattached content.

        """
        #mediadir = os.path.join(writeto, "media")
        #if not os.path.exists(mediadir):
        #    os.makedirs(mediadir)

        root = Element("site")
        root.set('version', str(self.VERSION))
        root.set('base', base)
        files = self.export_node(root, node)

        from .models import Configuration
        ## Import the configuration module so the registration of the
        ## default config takes place
        from . import configuration

        defaultconfig = Configuration.config()

        
        for (related, (label, model, formclass)) in \
            configuration_registry.iteritems():

            configxml = SubElement(root, "config")
            configxml.attrib["set"] = related


            if related:
                try:
                    config = getattr(defaultconfig, related).get()
                except model.DoesNotExist:
                    continue
            else:
                config = defaultconfig

            for field in config._meta.concrete_model._meta.fields:
                fieldxml = SubElement(configxml, "item", dict(name=field.name))

                fieldxml.text = field.value_to_string(config)

        return root, files

class Importer(object):
    def __init__(self, basenode=None, verbose=0, update_lm=True):
        self.verbose = verbose
        self.basenode = basenode or Node.root()
        self.update_lm = update_lm

    def import_node(self, node, tree):
        
        # import pytest;pytest.set_trace()
        paths = {}
        contents = []
        delays = []

        for content in tree.findall("content"):
            typename = content.attrib['type']
            slug = content.attrib['slug']
            spoke = type_registry.get(typename)
            fields = content.find("fields")

            language = None
            for field in fields.findall("field"):
                if field.attrib.get('name') == 'language':
                    language = field.text

            s, cdelays = spoke.serializer(self.basenode, update_lm=self.update_lm
                                        ).deserialize(spoke, fields)
            delays.extend(cdelays)

            paths[language] = slug
            contents.append((language, s.instance))

            #if slug == "":
            #    n = node
            #else:
            #    n = node.add(slug)
            #n.set(s.instance, language=language)

        if contents:
            ## Add on root in stead of new node
            if paths.values()[0] == "":
                n = node
            elif paths.keys()[0] is None:
                n = node.add(paths[None])
            else:
                n = node.add(langslugs=paths)

            for lang, cont in contents:
                n.set(cont, language=lang)

        if tree.find("children") is not None:
            for child in tree.find("children"):
                sub_delays = self.import_node(n, child)
                delays.extend(sub_delays)


        return delays

    def run(self, tree, base=""):
        version = tree.attrib['version']
        xmlbase = tree.attrib['base']
        # import pytest; pytest.set_trace()
        delays = []

        for node in tree.findall("node"):
            subdelays = self.import_node(self.basenode, node)
            delays.extend(subdelays)

        for delay in delays:
            delay()

        # import ipdb; ipdb.set_trace()

        from .models import Configuration
        for configxml in tree.findall("config"):
            defaultconfig = Configuration.config()
            related = configxml.attrib.get('set', '')

            if related:
                c = configuration_registry.get(related)
                if not c:
                    continue
                (label, model, formclass) = c
                try:
                    config = getattr(defaultconfig, related).get()
                except model.DoesNotExist:
                    config = model(main=defaultconfig)
            else:
                config = defaultconfig

            for field in configxml.findall("item"):
                field_name = field.attrib.get("name")
                if field_name in ("id", "main"):
                    continue  ## skip internal / key fields
                field_value = field.text or ""
                setattr(config, field_name, field_value)

            config.save()
