from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from wheelcms_axle import node

class NodeAdmin(GuardedModelAdmin):
    model = node.Node

class PathsAdmin(GuardedModelAdmin):
    model = node.Paths

admin.site.register(node.Node, NodeAdmin)
admin.site.register(node.Paths, PathsAdmin)
