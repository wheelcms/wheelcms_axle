from . import access

class WheelHandlerMixin(object):
    def hasaccess(self):
        user = self.user()
        return access.has_access(user, self.instance)
