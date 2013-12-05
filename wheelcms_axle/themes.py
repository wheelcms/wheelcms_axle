from wheelcms_axle.registry import Registry
from django.conf import settings

class Theme(object):
    DEFAULT_JS = "bootstrap.js"

    def __init__(self, id, name, css, js=[], extra=""):
        self.id = id
        self.name = name
        if isinstance(css, (str, unicode)):
            self._css = ["wheel_content.css", css]
        else:
            self._css = ["wheel_content.css"] + list(css)

        if isinstance(js, (str, unicode)):
            self._js = [js or self.DEFAULT_JS]
        else:
            self._js = js

        self.extra = extra


    def css_resources(self):
        return ["%s/css/%s" % (settings.STATIC_URL, f) for f in self._css]

    def js_resources(self):
        return ["%s/js/%s" % (settings.STATIC_URL, f) for f in self._js]

    def css(self):
        return "\n".join('<link rel="stylesheet" href="%s"' \
               ' media="screen, projection, print"/>' % \
               r for r in self.css_resources())

    def js(self):
        return "\n".join('<script src="%s"></script>' % \
               r for r in self.js_resources())


class ThemeRegistry(list):
    def register(self, theme):
        self.append(theme)

    def find(self, id):
        for t in self:
            if t.id == id:
                return t
        return None


theme_registry = Registry(ThemeRegistry())

theme_registry.register(Theme('default', 'Bootstrap', "bootstrap.min.css"))
