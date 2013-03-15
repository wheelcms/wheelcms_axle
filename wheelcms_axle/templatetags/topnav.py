from django import template

from wheelcms_axle import queries

register = template.Library()

@register.inclusion_tag('wheelcms_axle/topnav.html', takes_context=True)
def topnav(context):
    context = context.get('instance')

    nav = []

    ## Find top/secondlevel published nodes in one query XXX
    for toplevel in queries.toplevel_visible_children():
        ## make sure /foo/bar does not match in /football by adding the /
        item = dict(active=False, node=toplevel)

        if toplevel == context or \
           (context and context.path.startswith(toplevel.path + '/')):
            item = dict(active=True, node=toplevel)

        sub = []
        for secondlevel in queries.get_visible_children(toplevel):
            sub.append(secondlevel)

        item['sub'] = sub
        nav.append(item)
    return dict(toplevel=nav)
