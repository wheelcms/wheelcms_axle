from django import template

from wheelcms_axle import queries
from wheelcms_axle.utils import get_active_language

register = template.Library()

@register.inclusion_tag('wheelcms_axle/topnav.html', takes_context=True)
def topnav(context):
    node = context.get('instance')
    request = context.get('request')
    language = get_active_language(request)

    nav = []

    ## Find top/secondlevel published nodes in one query XXX
    for toplevel in queries.toplevel_visible_children(language=language):
        ## make sure /foo/bar does not match in /football by adding the /
        item = dict(active=False, node=toplevel)
        content = toplevel.content(language=language)
        item['url'] = toplevel.get_absolute_url(language=language)
        item['title'] = content.title if content else ""

        if toplevel == node or \
           (node and node.path.startswith(toplevel.path + '/')):
            item['active'] = True

        sub = []
        for secondlevel in queries.get_visible_children(toplevel, language=language):
            slitem = dict(node=secondlevel)
            content = secondlevel.content(language=language)
            slitem['url'] = secondlevel.get_absolute_url(language=language)
            slitem['title'] = content.title if content else ""

            sub.append(slitem)

        item['sub'] = sub
        nav.append(item)
    return dict(toplevel=nav)
