from django.core.management.base import BaseCommand

from wheelcms_axle.models import Node

from wheelcms_axle.impexp import Exporter

from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class Command(BaseCommand):
    """ Normalize existing usernames to match allowed characters """
    args = 'path'
    help = 'Export (part of) a site as XML'

    def handle(self, path="", *args, **options):
        base = path # "" # /sub5_2/sub4_2/sub3_2"
        root = Node.get(base)
        xml = Exporter().run(root, base)
        print prettify(xml)
