import mimetypes
import re
import os
import datetime

from django.db import models, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User

from userena.models import UserenaLanguageBaseProfile

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

@receiver(post_save, sender=User)
def log_create(sender, instance, created, **kwargs):
    """ Log the creation of a new user """
    if created:
        stracks.user(instance).log("? has been created")
    ## make sure it has a wheel profile
    WheelProfile.objects.get_or_create(user=instance)


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

