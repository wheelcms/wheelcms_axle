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

        if not os.access(settings.MEDIA_ROOT, os.W_OK):
            print "%s may not be writable. Continue (y/n)?" % settings.MEDIA_ROOT
            if raw_input().lower().strip() != "y":
                print "Exiting"
                return

        data = open(contentxml).read()
        tree = ElementTree.fromstring(data)
        root = Node.root() ## allow relative base XXX
        Importer().run(root, tree)

        ## check writability
        copy_tree(mediadir, settings.MEDIA_ROOT)

