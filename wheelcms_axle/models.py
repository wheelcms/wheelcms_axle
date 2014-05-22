import mimetypes
import re
import os
import datetime

from django.db import models, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User, Group

from userena.models import UserenaLanguageBaseProfile

from drole.fields import RoleField

from .impexp import WheelSerializer
from .themes import theme_registry

## import pytz

from django.utils.translation import ugettext as _

class WheelProfile(UserenaLanguageBaseProfile):
    """ timezone, ... ?
    """
    ##timezone = models.CharField(max_length=100, default=config.DEFAULT_TIMEZONE,
    ##    choices=[(x, x) for x in pytz.common_timezones])
    inform = models.BooleanField(default=False)
    user = models.OneToOneField(User,
                                unique=True,
                                verbose_name=_('user'),
                                related_name='my_profile')

    twitter = models.TextField(blank=True, null=False, default="")
    google = models.TextField(blank=True, null=False, default="")
    linkedin = models.TextField(blank=True, null=False, default="")

## backwards compat, should import from node directly
from .node import NodeException, DuplicatePathException, InvalidPathException
from .node import NodeInUse, CantRenameRoot, NodeBase
from .node import WHEEL_NODE_BASECLASS
from .node import Node

from .content import ContentClass, ContentBase
from .content import WHEEL_CONTENT_BASECLASS
from .content import Content, ClassContentManager
from .content import FileContent, ImageContent
from .content import type_registry

class Configuration(models.Model):
    title = models.CharField(max_length=256, blank=True, null=False, default="")
    description = models.TextField(blank=True, null=False, default="")
    theme = models.CharField(max_length=256, blank=True, null=False, default="default")

    analytics = models.CharField(max_length=50, blank=True, null=False, default="")
    head = models.TextField(blank=True, null=False, default="")

    sender = models.CharField(max_length=100, blank=True, null=False, default="")
    sendermail = models.EmailField(max_length=100, blank=True, null=False, default="")
    mailto = models.EmailField(max_length=100, blank=True, null=False, default="")

    @classmethod
    def config(cls):
        """ singleton-ish pattern """
        try:
            instance = Configuration.objects.all()[0]
        except IndexError:
            instance = Configuration()
            instance.save()
        return instance

    def themeinfo(self):
        """ resolve self.theme into a Theme instance """
        return theme_registry.find(self.theme)


class Role(models.Model):
    """
        System-wide (non-local) roles for users
    """
    role = RoleField(max_length=255, blank=False)
    user = models.ForeignKey(User, related_name="roles", null=True, blank=True)
    group = models.ForeignKey(Group, related_name="roles", null=True, blank=True)

#class ConfigItem(models.Model):
#    name = models.CharField(max_length=256, blank=False, null=False)
#    value = models.TextField(blank=True, null=False, default="")
#    type = models.CharField(max_length=256, blank=False, null=False,
#                            default="string")
#    ns = models.CharField(max_length=256, blank=True, null=False,
#                          default="default")
#    configuration = models.ForeignKey(Configuration, related_name="items",
#                           blank=False, null=False)

## signals for login/logout logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from userena.signals import signup_complete
from django.contrib.auth.signals import user_logged_in, user_logged_out

import stracks
## django 1.5
## from django.contrib.auth.signals import user_login_failed
## 
## @receiver(user_login_failed)
## def log_failure(sender, credentials, **kwargs):
##     """ Log the user logging out """
##     stracksclient.warning("Authentication failed", data=credentials)
##

from django.db.utils import DatabaseError
import logging

@receiver(post_save, sender=User)
def log_create(sender, instance, created, **kwargs):
    """ Log the creation of a new user """
    if created:
        stracks.user(instance).log("? has been created")
    ## make sure it has a wheel profile
    try:
        WheelProfile.objects.get_or_create(user=instance)
    except DatabaseError:
        logging.error("Failed to create profile for %s, perhaps migrations haven't run yet?" % instance)
        from django.db import connection
        connection._rollback()

from south.signals import post_migrate

@receiver(post_migrate)
def create_profiles(app, **kwargs):
    if app == "wheelcms_axle":
        for u in User.objects.all():
            WheelProfile.objects.get_or_create(user=u)

@receiver(signup_complete, dispatch_uid='stracks.log_signup')
def log_signup(sender, signal, user, **kwargs):
    """ Log the creation of a new user """
    stracks.user(user).log("? has completed (userena) signup")


@receiver(user_logged_in, dispatch_uid='stracks.log_signin')
def log_login(sender, request, user, **kwargs):
    """ Log the user logging in """
    stracks.user(user).log("? has logged in", action=stracks.login())

@receiver(user_logged_out, dispatch_uid='stracks.log_signout')
def log_logout(sender, request, user, **kwargs):
    """ Log the user logging out """
    stracks.user(user).log("? has logged out", action=stracks.logout())

@receiver(post_save, dispatch_uid="wheelcms_axle.spoke.assign_perms")
def assign_perms(sender, instance, created, **kwargs):
    
    if issubclass(sender, Content):
        spoke = instance.spoke()
        if spoke:
            spoke.assign_perms()
            if created:
                wf = spoke.workflow()
                state = instance.state
                assignment = wf.permission_assignment.get(state)
                if assignment:
                    spoke.update_perms(assignment)

    if hasattr(sender, 'permission_assignment') and created:
        assign_perms(instance, instance.permission_assignment)

## Give new user additional userena permissions
from userena.managers import ASSIGNED_PERMISSIONS
from guardian.shortcuts import assign_perm
from guardian.models import Permission

@receiver(post_save, sender=User, dispatch_uid='userena.created.permissions')
def user_created(sender, instance, created, raw, using, **kwargs):
    """ Adds 'change_profile' permission to created user objects """
    ## Ignore missing permissions - nothing we can do about it.
    if created:
        for perm in ASSIGNED_PERMISSIONS['profile']:
            try:
                assign_perm(perm[0], instance, instance.get_profile())
            except Permission.DoesNotExist:
                pass

        # Give permissions to view and change itself
        for perm in ASSIGNED_PERMISSIONS['user']:
            try:
                assign_perm(perm[0], instance, instance)
            except Permission.DoesNotExist:
                pass

