import os
import shutil
from optparse import make_option

from xml.etree import ElementTree
from xml.dom import minidom

from django.core.management.base import BaseCommand, CommandError
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
    args = '[folder-to-export-to]'
    help = 'Export (part of) a site as XML'

    base_options = (
        make_option("-q", "--quiet", action="store_false", dest="verbose",
                    default=True, help="Be quiet"),
    )

    option_list = BaseCommand.option_list + base_options

    def handle(self, writeto=None, path="", *args, **options):
        if writeto is None:
            raise CommandError("You must specificy a writable directory where the export can be written to")

        verbose = options.get('verbose', True)

        mediadir = os.path.join(writeto, "media")
        if not os.path.exists(mediadir):
            os.makedirs(mediadir)

        base = path # "" # /sub5_2/sub4_2/sub3_2"
        root = Node.get(base)
        xml, files = Exporter().run(root, base)
        open(os.path.join(writeto, "content.xml"), "w"
            ).write(prettify(xml).encode("utf8"))
        for file in set(files):
            dirname = os.path.dirname(file)
            if dirname:
                dir = os.path.join(mediadir, dirname)
                if not os.path.exists(dir):
                    os.makedirs(dir)
            dest = os.path.join(mediadir, file)
            source = os.path.join(settings.MEDIA_ROOT, file)

            if verbose:
                print "Copy %s to %s" % (source, dest)
            shutil.copy(source, dest)

        if verbose:
            print files
