from wheelcms_axle.registry import Registry
from django.conf import settings

class Theme(object):
    DEFAULT_JS = "bootstrap.js"

    def __init__(self, id, name, css, js=None):
        self.id = id
        self.name = name
        self._css = css
        self._js = js or self.DEFAULT_JS

    def css(self):
        return '<link rel="stylesheet" href="%s/css/%s"' \
               'media="screen, projection, print"/>' % \
               (settings.STATIC_URL, self._css)

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
