def has_access(user, instance=None):
    return user.is_active and (user.is_superuser or
                               user.groups.filter(name="managers").exists())
