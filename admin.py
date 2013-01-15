from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from wheelcms_axle import models

class NodeAdmin(GuardedModelAdmin):
    model = models.Node


admin.site.register(models.Node, NodeAdmin)
