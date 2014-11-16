
import os
from distutils.dir_util import copy_tree
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import models
from wheelcms_axle.content import Content, type_registry
from wheelcms_axle import auth

from drole.models import RolePermission

class Command(BaseCommand):
    """ Generate permission/role mappings for all content """
    help = "Generate permission/role mappings for all content "

    base_options = (
        make_option("-q", "--quiet", action="store_false", dest="verbose",
                    default=True, help="Be quiet"),
    )
    option_list = BaseCommand.option_list + base_options


    def handle(self, *args, **options):
        verbose = options.get('verbose', True)

        permissions = args
        ## Check if there are any assignments, optionally skip those?
        ## if the state is published, fix view perm XXX
        ## (or even better: properly define and consult workflow)
        for m in models.get_models(include_auto_created=True):
            if not issubclass(m, Content) or not type_registry.get(m.get_name()):
                continue

            for c in m.objects.all():
                s = c.spoke()
                wf = s.workflow()
                state = c.state
                wfassignment = wf.permission_assignment.get(state)

                for permission in map(auth.Permission, permissions):
                    classassignment = getattr(s, "permission_assignment",
                                              {}).get(permission)
                    if not classassignment:
                        continue

                    assignments = RolePermission.assignments(c).filter(permission=permission)
                    if assignments.count() == 0:
                        if verbose:
                            print c.title, s, "has no assignment for", permission
                        for role in classassignment:
                            RolePermission.assign(c, role, permission).save()

                        if wfassignment and wfassignment.get(permission):
                            s.update_perms(c, {permission:wfassignment[permission]})

