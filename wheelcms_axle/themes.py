from wheelcms_axle.registry import Registry
from django.conf import settings

class Theme(object):
    DEFAULT_JS = "bootstrap.js"

    def __init__(self, id, name, css, js=None):
        self.id = id
        self.name = name
        ## XXX handle case when multiple css files are passed
        self._css = ["wheel_content.css", css]
        self._js = js or self.DEFAULT_JS

    def css_resources(self):
        return ["%s/css/%s" % (settings.STATIC_URL, f) for f in self._css]

    def css(self):
        return "\n".join('<link rel="stylesheet" href="%s"' \
               ' media="screen, projection, print"/>' % \
               r for r in self.css_resources())

    def js(self):
        return '<script src="%s/js/%s"></script>' % \
               (settings.STATIC_URL, self._js)


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
