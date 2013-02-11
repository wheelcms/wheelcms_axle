import mimetypes
import re
import os
import datetime

from django.db import models, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User

from userena.models import UserenaLanguageBaseProfile

from .impexp import WheelSerializer
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
    title = models.CharField(max_length=256, blank=False)
    description = models.TextField(blank=True)
    theme = models.CharField(max_length=256, blank=True, default="default")

    @classmethod
    def config(cls):
        """ singleton-ish pattern """
        try:
            instance = Configuration.objects.all()[0]
        except IndexError:
            instance = Configuration()
            instance.save()
        return instance


