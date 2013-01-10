from wheelcms_axle.models import Node

def get_visible_children(node):
    """
        Return all childen of a node that
        are published and in navigation,
        ordered by position
    """
    return node.childrenq(contentbase__state="published",
                          contentbase__navigation=True)

def toplevel_visible_children():
    """
        Return all toplevel visible nodes
    """
    return get_visible_children(Node.root())
