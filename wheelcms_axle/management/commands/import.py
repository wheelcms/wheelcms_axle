import os
from distutils.dir_util import copy_tree

from xml.etree import ElementTree
from django.core.management.base import BaseCommand
from django.conf import settings

from wheelcms_axle.models import Node

from wheelcms_axle.impexp import Importer


class Command(BaseCommand):
    """ Import xml """
    args = 'readfrom [path]'
    help = 'Import an xml dump'

    def handle(self, readfrom, path="", *args, **options):
        contentxml = os.path.join(readfrom, "content.xml")
        mediadir = os.path.join(readfrom, "media")

        data = open(contentxml).read()
        tree = ElementTree.fromstring(data)
        root = Node.root() ## allow relative base XXX
        Importer().run(root, tree)

        copy_tree(mediadir, settings.MEDIA_ROOT)

