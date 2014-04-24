from . import roles

def has_access(user, instance=None):
    if user.is_anonymous():
        return False
    if not user.is_active:
        return False
    if user.is_superuser:
        return True
    return roles.admin in [r.role for r in user.roles.all()]
