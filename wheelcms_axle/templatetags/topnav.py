from django import template

from wheelcms_axle import queries

register = template.Library()

@register.inclusion_tag('wheelcms_axle/topnav.html', takes_context=True)
def topnav(context):
    context = context.get('instance')

    toplevel = []

    for child in queries.toplevel_visible_children():
        ## make sure /foo/bar does not match in /football by adding the /
        if context is None:
            toplevel.append(dict(active=False, node=child))
        elif child == context or context.path.startswith(child.path + '/'):
            toplevel.append(dict(active=True, node=child))
        else:
            toplevel.append(dict(active=False, node=child))
    return dict(toplevel=toplevel)
