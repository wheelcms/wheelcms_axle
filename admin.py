from django.contrib import admin
from wheelcms_axle import models

class NodeAdmin(admin.ModelAdmin):
    model = models.Node


admin.site.register(models.Node, NodeAdmin)
