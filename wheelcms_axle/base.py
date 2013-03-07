class WheelHandlerMixin(object):
    def hasaccess(self):
        user = self.user()
        return user.is_active and (user.is_superuser or
                                   user.groups.filter(name="managers").exists())


