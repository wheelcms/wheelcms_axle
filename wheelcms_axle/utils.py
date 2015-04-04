import json as jsonlib
from django.http import HttpResponse
from django.conf import settings

from wheelcms_axle import translate
from wheelcms_axle import locale


def get_active_language():
    """
        The active language is either forced in settings,
        set in the session (for admin), a GET argument or
        the translation default
    """
    lang = getattr(settings, 'FORCE_LANGUAGE', None)

    if not lang:
        lang = locale.get_content_language()

    langids = (l[0] for l in translate.languages())

    if lang not in langids and getattr(settings, 'FALLBACK', None):
        lang = settings.FALLBACK
    return lang

def generate_slug(name, language="en", max_length=100,
                  allowed="abcdefghijklmnopqrstuvwxyz0123456789_-",
                  default="slug"):
    """ generate a slug based on a title / sentence """
    from wheelcms_axle.stopwords import stopwords
    import re

    name = name.lower()
    name_no_stopwords = " ".join(x for x in name.split()
                                 if x not in set(stopwords.get(language, [])))
    slug = re.sub("[^%s]+" % allowed, "-",
                          name_no_stopwords,
                          )[:max_length].strip("-")
    slug = re.sub("-+", "-", slug)
    return slug or default

def json(f):
    def jsonify(*args, **kw):
        return HttpResponse(jsonlib.dumps(f(*args, **kw)),
                            mimetype="application/json")
    return jsonify

def applyrequest(f=None, **kw):
    """
        Support the following forms:
        @applyrequest
        @applyrequest()
        @applyrequest(page=int)

        by wrapping the appropriate decorator depending on wether a function
        was passed or not
    """
    if not f:
        def x(f):
            return applyrequest_notype(f, **kw)
        return x
    else:
        return applyrequest_notype(f)

def applyrequest_notype(f, **mapping):
    ## XXX positional arguments don't work, see reset.py -> process
    def applicator(self, *args, **kw):
        ##
        ## Improvements: figure out which arguments don't
        ## have defaults, provide proper error if missing
        request = self.request
        vars = f.func_code.co_varnames[:f.func_code.co_argcount]
        args = args[:]
        kw = kw.copy()
        for k in vars:
            try:
                v = request.REQUEST[k]
                if k in mapping:
                    v = mapping[k](v)
                kw[k] = v
            except KeyError:
                pass

        return f(self, *args, **kw)

    return applicator

def applyrequest_type(**kw):
    """
        A decorator that applies request arguments to the method,
        supporting an additional mapping. E.g.

        @applyrequest_type(page=int)
        def get(page=1):
            ...

        will get a variable 'page' from the request and convert it to int
    """
    def x(f):
        return applyrequest(f, **kw)
    return x

def classproperty(f):
    """
        E.g.
        >>> class foo(object):
        ...    @classproperty
        ...    def name(cls):
        ...        return cls.__name__
        >>> print foo.name 
        'foo'
    """
    class name(object):
        def __init__(self, getter):  
            self.getter = getter

        def __get__(self, obj, type=None):
            return self.getter(type)
    return name(f)
