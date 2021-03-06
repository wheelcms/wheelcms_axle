
import os
from distutils.dir_util import copy_tree
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import models
from wheelcms_axle.content import Content, type_registry
from wheelcms_axle import auth

class Command(BaseCommand):
    """ Generate permission/role mappings for all content """
    help = "Generate permission/role mappings for all content "

    base_options = (
        make_option("-q", "--quiet", action="store_false", dest="verbose",
                    default=True, help="Be quiet"),
    )
    option_list = BaseCommand.option_list + base_options


    def handle(self, **options):
        ## Check if there are any assignments, optionally skip those?
        ## if the state is published, fix view perm XXX
        ## (or even better: properly define and consult workflow)
        for m in models.get_models(include_auto_created=True):
            if issubclass(m, Content) and type_registry.get(m.get_name()):
                for c in m.objects.all():
                    s = c.spoke()
                    print "(spoke) Assigning", s
                    s.assign_perms()

                    wf = s.workflow()
                    state = c.state
                    assignment = wf.permission_assignment.get(state)
                    if assignment:
                        print "(spoke) Updating to state", state
                        s.update_perms(assignment)
            elif hasattr(m, 'permissions_assignment'):
                for i in m.objects.all():
                    print "(instance) Assigning", i
                    auth.assign_perms(i, i.permissions_assignment)

