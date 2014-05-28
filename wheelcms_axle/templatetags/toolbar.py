from django import template
from django.template.loader import render_to_string

register = template.Library()


from wheelcms_axle.toolbar import get_toolbar

@register.tag(name="toolbar")
def toolbar(parser, token):
    return ToolbarNode()

class ToolbarNode(template.Node):
    def render(self, context):
        return render_to_string("wheelcms_axle/toolbar.html",
                          {'toolbar':get_toolbar()},
                          context_instance=context)


@register.tag(name="toolbar_action")
def toolbar_action(parser, token):
    try:
        tagname, actionvar = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
                    "{0} tag requires argument".format(token.contents[0]))
    return ActionNode(actionvar)


class ActionNode(template.Node):
    def __init__(self, actionvar):
        self.actionvar = actionvar

    def render(self, context):
        val = context[self.actionvar]

        return val.render(context)
