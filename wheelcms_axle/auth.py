from drole.types import Role as droleRole, Permission as drolePermission
from drole.models import RolePermission

class require(object):
    def __init__(self, permission):
        self.permission = permission

    def __call__(self, f):
        def wrapped(handler, *args, **kwargs):
            request = getattr(handler, 'request')
            if request:
                user = request.user

                return f(*args, **kwargs)
            return handler.forbidden()
        return wrapped

def assign(assignment):
    """
        A decorator to assign or extend a role/permission mapping to a
        class. It wil take any existing (inherited) assignment, copy it
        and update it. E.g.

        @assign({'a':1, 'b':2})
        class T(object):
            pass

        @assign({'a':2, 'c':3})
        class Tchild(T):
            pass
    """
    def klasswrapper(k):
        _assignment = getattr(k, 'permission_assignment', {}).copy()
        _assignment.update(assignment)
        k.permission_assignment = _assignment
        return k
    return klasswrapper


def Permission(id, name="", description=""):
    return drolePermission.create(id, name, description)

def Role(id, name="", description=""):
    return droleRole.create(id, name, description)

def assign_perms(instance, permdict):
    """ invoked by a signal handler upon creation: Set initial
        permissions """
    for permission, roles in permdict.iteritems():
        for role in roles:
            RolePermission.assign(instance, role, permission).save()

def update_perms(instance, permdict):
    for permission, roles in permdict.iteritems():
        RolePermission.clear(instance, permission)
        for role in roles:
            RolePermission.assign(instance, role, permission).save()

def get_roles_in_context(request, type, spoke=None):
    ## check roles for request.user and their group(s), local roles, owner role
    from wheelcms_axle import roles
    r = [roles.anonymous]
    if request.user.is_authenticated():
        r.append(roles.member)
        r.extend(r.role for r in request.user.roles.all())

        for g in request.user.groups.all():
            r.extend(r.role for r in g.roles.all())

        if spoke and spoke.instance and spoke.instance.owner == request.user:
            r.append(roles.owner)

    if request.user.username == 'ivo':
        r.extend([roles.admin, roles.member])
    elif request.user.username == 'admin':
        r.append(roles.member)
    return set(r)

def has_access(request, type, spoke, permission):
    if request.user.is_authenticated() and not request.user.is_active:
        return False

    if request.user.is_active and request.user.is_superuser:
        return True

    roles = get_roles_in_context(request, type, spoke)
    if spoke and spoke.instance:
        for role in roles:
            if role.has_access(spoke.instance, permission):
                return True

    ## (ab)use Spoke as holder for global permissions
    from wheelcms_axle.spoke import Spoke

    type = type or Spoke
    ## Should there be a fallback to class permissions?
    classperm = type.permission_assignment.get(permission, ())

    if set(roles) & set(classperm):
        return True

    return False
