import os
import shutil

from xml.etree import ElementTree
from xml.dom import minidom

from django.core.management.base import BaseCommand
from django.conf import settings

from wheelcms_axle.models import Node

from wheelcms_axle.impexp import Exporter


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class Command(BaseCommand):
    """ Normalize existing usernames to match allowed characters """
    args = 'writeto [path]'
    help = 'Export (part of) a site as XML'

    def handle(self, writeto, path="", *args, **options):
        mediadir = os.path.join(writeto, "media")
        if not os.path.exists(mediadir):
            os.makedirs(mediadir)

        base = path # "" # /sub5_2/sub4_2/sub3_2"
        root = Node.get(base)
        xml, files = Exporter().run(root, base)
        open(os.path.join(writeto, "content.xml"), "w").write(prettify(xml))
        for file in set(files):
            dirname = os.path.dirname(file)
            if dirname:
                dir = os.path.join(mediadir, dirname)
                if not os.path.exists(dir):
                    os.makedirs(dir)
            dest = os.path.join(mediadir, file)
            source = os.path.join(settings.MEDIA_ROOT, file)

            print "Copy %s to %s" % (source, dest)
            shutil.copy(source, dest)

        print files
