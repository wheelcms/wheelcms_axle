class WheelPermission(object):
    def __init__(self, id, name="", description=""):
        self.id = id
        self.name = name or id
        self.description = description

_permission_registry = {}
def Permission(id, name="", description=""):
    p = _permission_registry.get(id)
    if p is None:
        p = WheelPermission(id, name, description)
        _permission_registry[id] = p
    return p

class WheelRole(object):
    def __init__(self, id, name="", description=""):
        self.id = id
        self.name = name or id
        self.description = description

_role_registry = {}
def Role(id, name="", description=""):
    r = _role_registry.get(id)
    if r is None:
        r = WheelRole(id, name, description)
        _role_registry[id] = r
    return r


def has_access(request, type, instance, permission):
    return True

    for i in ("first try", "second try"):
        try:
            do_request_depending_on_perm_exists
            return success_or_failure
        except drolePerm.DoesNotExist:
            dit_gaat_zo_niet_werken_filter().succeed_gewoon
            create_the_perm
    return False

