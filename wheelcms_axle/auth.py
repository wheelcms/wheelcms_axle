from drole.models import Role as droleRole, Permission as drolePermission
from drole.models import RolePermission

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

def get_roles_in_context(request, type, instance=None):
    ## check roles for request.user and their group(s), local roles, owner role
    from wheelcms_axle import roles
    r = [roles.anonymous]
    if request.user.username == 'ivo':
        r.extend([roles.admin, roles.member])
    elif request.user.username == 'admin':
        r.append(roles.member)
    return set(r)

def has_access(request, type, instance, permission):
    roles = get_roles_in_context(request, type, instance)
    if instance:
        for role in roles:
            if role.has_access(instance, permission):
                return True

    ## Should there be a fallback to class permissions?
    classperm = type.permission_assignment.get(permission, ())


    if set(roles) & set(classperm):
        return True

    return False
