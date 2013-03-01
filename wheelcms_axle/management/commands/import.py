from django.core.management.base import BaseCommand

from wheelcms_axle.models import Node

from wheelcms_axle.impexp import Importer

from xml.etree import ElementTree

class Command(BaseCommand):
    """ Import xml """
    args = 'path'
    help = 'Import an xml dump'

    def handle(self, path="", *args, **options):
        data = open(path).read()
        tree = ElementTree.fromstring(data)
        root = Node.root() ## allow relative base XXX
        Importer().run(root, tree)
