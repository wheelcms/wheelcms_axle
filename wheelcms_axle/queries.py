from wheelcms_axle.models import Node

def get_visible_children(node, language=None):
    """
        Return all childen of a node that
        are published and in navigation,
        ordered by position
    """
    ## published state no longer determines visibility; permissions do
    ## (which are controlled by workflow state)
    q = dict(contentbase__navigation=True)
    if language:
        q['contentbase__language'] = language

    return node.childrenq(**q)

def toplevel_visible_children(language=None):
    """
        Return all toplevel visible nodes
    """
    return get_visible_children(Node.root(), language=language)
