from warnings import warn
from . import access

class WheelHandlerMixin(object):
    def hasaccess(self):
        """ hasaccess is obsolete and should be replaced with a more
            fine grained permission access. For backward compatibility,
            verify the user has the admin role
        """
        warn("WheelHandlerMixin.hasaccess is obsolete; use auth.has_access",
             DeprecationWarning)

        return access.has_access(self.user())
