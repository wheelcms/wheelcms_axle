from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import re
import random

from wheelcms_axle.models import Node
from wheelcms_spokes.models import Page

class Command(BaseCommand):
    """ Normalize existing usernames to match allowed characters """
    args = ''
    help = 'setup simple content structure'

    def handle(self, *args, **options):
        """ Usage ../bin/django clean_usersnames (0|1) """
        root = Node.root()
        main = Page(title="Welcome", body="This is the main page")
        main.save()
        root.set(main)

        c1 = root.add('sub')
        sub = Page(title="Subpage", body="I'm a sub page")
        sub.save()
        c1.set(sub)

