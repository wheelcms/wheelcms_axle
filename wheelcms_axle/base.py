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

from django.views.generic import View
from django.http import HttpResponse, Http404
from django.template import RequestContext, loader
from . import access
from warnings import warn

class WheelView(View):
    def user(self):
        ## deprecate?

        return self._user

    def dispatch(self, request, *args, **kwargs):
        self._user = request.user
        self.context = RequestContext(request)

        return super(WheelView, self).dispatch(request, *args, **kwargs)

    def get_template(self, t):
        return loader.get_template(t)

    def render_template(self, t, **kw):
        template_path = t
        self.context.push()
        self.context.update(kw)
        t = self.get_template(template_path)
        result = t.render(self.context)
        self.context.pop()

        ## Replace <[ ]> markers to {{ }} markers
        result = result.replace("<[", "{{").replace("]>", "}}")
        return result

    def template(self, t, **kw):
        return HttpResponse(self.render_template(t, **kw))

    def hasaccess(self):
        """ hasaccess is obsolete and should be replaced with a more
            fine grained permission access. For backward compatibility,
            verify the user has the admin role
        """
        warn("WheelView.hasaccess is obsolete; use auth.has_access",
             DeprecationWarning)

        return access.has_access(self.user())

