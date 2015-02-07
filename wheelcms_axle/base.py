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
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest, HttpResponseServerError
import settings
import urllib

class BaseException(Exception):
    pass

class Redirect(BaseException):
    def __init__(self, url, permanent=False):
        self.url = url
        self.permanent = permanent

class NotFound(BaseException):
    pass

class Forbidden(BaseException):
    pass

class BadRequest(BaseException):
    pass

class ServerError(BaseException):
    pass

class WheelView(View):
    ## special results
    @classmethod
    def notfound(cls):
        raise NotFound()

    @classmethod
    def forbidden(cls):
        raise Forbidden()

    @classmethod
    def badrequest(cls):
        raise BadRequest()

    @classmethod
    def servererror(cls):
        raise ServerError()

    def redirect(self, url, permanent=False, hash=None,
                 piggyback=False, **kw):
        args = kw.copy()
        if piggyback:
            args.update(self.context['piggyback'])
        ## encode args values to utf8
        encoded = {}
        for (k, v) in args.iteritems():
            if isinstance(v, unicode):
                v = v.encode('utf8')
            encoded[k] = v
        args = urllib.urlencode(encoded)
        if args:
            if '?' in url: # it already has args
                url = url + "&" + args
            else:
                url = url + "?" + args
        if hash:
            url += "#" + hash
        raise Redirect(url, permanent=permanent)

    @classmethod
    def url_actions(cls):
        ## add callable check?
        return [x[7:] for x in dir(cls) if x.startswith("handle_")] + \
               [x for x in dir(cls) if getattr(x, 'ishandler', False)]  + \
               ["create", "edit"]

    def user(self):
        ## deprecate?

        return self._user

    def dispatch(self, request, *args, **kwargs):
        self._user = request.user
        self.context = RequestContext(request)

        try:
            return super(WheelView, self).dispatch(request, *args, **kwargs)
        except Redirect, e:
            if e.permanent:
                return HttpResponsePermanentRedirect(e.url)
            else:
                return HttpResponseRedirect(e.url)
        except NotFound:
            raise Http404
        except Forbidden:
            return HttpResponseRedirect(settings.LOGIN_URL + "?next=" +
                                        urllib.pathname2url(request.path))
            #return HttpResponseForbidden()
        except BadRequest:
            return HttpResponseBadRequest()
        except ServerError:
            return HttpResponseServerError()

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

