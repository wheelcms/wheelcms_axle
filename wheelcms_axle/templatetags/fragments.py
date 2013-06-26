from django import template

from wheelcms_axle.registries.fragments import fragments_registry

"""
    Fragments allow child templates and (static) python code to inject fragments
    into (base) templates. This allows you to define generic fragments sections
    which can later be filled by either pythoncode (globally) or child templates
    (context specific)

    This is somewhat similar to django zekizai but it doesn't require the
    sections to be defined at the toplevel base template (but it does require
    a "{% block fragments %}")

    This is all somewhat experimental but seems to work :)
"""

register = template.Library()


@register.tag(name="fragment")
def fragment(parser, token):
    try:
        tag_name, fragmentname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument"
                                           % token.contents.split()[0])
    nodelist = parser.parse(("endfragment",))
    parser.delete_first_token()

    return FragmentBlockNode(fragmentname.strip("'\""), nodelist)


class FragmentBlockNode(template.Node):
    def __init__(self, fragmentname, nodelist):
        self.fragmentname = fragmentname
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        if self.fragmentname not in context.render_context:
            context.render_context[self.fragmentname] = []
        context.render_context[self.fragmentname].append(output)

        return ''


@register.tag(name="fragments")
def fragments(parser, token):
    try:
        tag_name, fragmentname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return FragmentNode(fragmentname.strip("'\""))


class FragmentNode(template.Node):
    def __init__(self, fragmentname):
        self.fragmentname = fragmentname

    def render(self, context):
        frags = fragments_registry.get(self.fragmentname, [])
        res = ""
        for f in sorted(frags):
            res += f[1]

        for nl in context.render_context.get(self.fragmentname, []):
            res += nl
        return res

