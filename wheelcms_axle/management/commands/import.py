import os
from distutils.dir_util import copy_tree
from optparse import make_option

from xml.etree import ElementTree
from django.core.management.base import BaseCommand
from django.conf import settings

from wheelcms_axle.models import Node

from wheelcms_axle.impexp import Importer


class Command(BaseCommand):
    """ Import XML content into WheelCMS """
    help = "Import content into WheelCMS"
    args = "file-or-directory"

    base_options = (
        make_option("-q", "--quiet", action="store_false", dest="verbose",
                    default=True, help="Be quiet"),
        make_option("--base", action="store", dest="base",
                    default="", help="Import into (sub) node. "
                                     "Create nodes if necessary"),
        make_option("--owner", action="store", dest="base",
                    default="", help="Default owner if owner is "
                                     "undefined or does not exist"),
        make_option("--no-update-lm", action="store_false", dest="update_lm",
                    default=True, help="Do not update the last modified date "
                                       "for imported content")

    )
    option_list = BaseCommand.option_list + base_options


    def handle(self, readfrom, update_lm=True, base="", owner="", **options):
        contentxml = os.path.join(readfrom, "content.xml")
        mediadir = os.path.join(readfrom, "media")

        if not os.access(settings.MEDIA_ROOT, os.W_OK):
            print "%s may not be writable. Continue (y/n)?" % settings.MEDIA_ROOT
            if raw_input().lower().strip() != "y":
                print "Exiting"
                return

        data = open(contentxml).read()
        tree = ElementTree.fromstring(data)
        basenode = Node.get(base)
        if basenode is None:
            basenode = Node.root()
            for part in base.strip("/").split("/"):
                sub = basenode.child(part)
                if sub is None:
                    sub = basenode.add(part)
                basenode = sub

        Importer(basenode, update_lm=update_lm).run(tree)

        ## check writability
        if os.path.exists(mediadir):
            copy_tree(mediadir, settings.MEDIA_ROOT)

