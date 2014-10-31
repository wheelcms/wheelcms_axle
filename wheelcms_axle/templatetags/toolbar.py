from django import template

from wheelcms_axle import queries
from wheelcms_axle.utils import get_active_language

from wheelcms_axle import auth

register = template.Library()

def navigation_items(request, node):
    language = get_active_language()

    nav = []

    ## remove visible_children? Unnecessary with permission checks

    ## Find top/secondlevel published nodes in one query XXX
    for toplevel in queries.toplevel_visible_children(language=language):
        ## make sure /foo/bar does not match in /football by adding the /
        item = dict(active=False, node=toplevel)
        content = toplevel.content(language=language)

        if content:
            spoke = content.spoke()
            perm = spoke.permissions.get('view')
            if not auth.has_access(request, spoke, spoke, perm):
                continue

        item['url'] = toplevel.get_absolute_url(language=language)
        item['title'] = content.title if content else ""

        if toplevel == node or \
           (node and node.path.startswith(toplevel.path + '/')):
            item['active'] = True

        sub = []
        for secondlevel in queries.get_visible_children(toplevel, language=language):
            slitem = dict(node=secondlevel)
            content = secondlevel.content(language=language)
            spoke = content.spoke()
            perm = spoke.permissions.get('view')
            if not auth.has_access(request, spoke, spoke, perm):
                continue

            slitem['url'] = secondlevel.get_absolute_url(language=language)
            slitem['title'] = content.title if content else ""

            sub.append(slitem)

        item['sub'] = sub
        nav.append(item)
    return dict(toplevel=nav)

@register.inclusion_tag('wheelcms_axle/topnav.html', takes_context=True)
def topnav(context):
    request = context.get('request')
    node = context.get('instance')

    return navigation_items(request, node)

from wheelcms_axle.toolbar import get_toolbar

@register.inclusion_tag("wheelcms_axle/toolbar.html", takes_context=True)
def toolbar(context):
    return dict(instance=context.get('instance'), toolbar=get_toolbar(), user=context.get('request').user)
