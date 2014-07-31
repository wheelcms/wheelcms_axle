class ContentContext(object):
    """
        A helper class that wraps content related stuff
        for easy access in templates
    """

    def __init__(self, content):
        self.content = content

    def title(self):
        ## deprecated through __getattr__
        return self.content.instance.title

    def url(self):
        return self.content.instance.get_absolute_url()

    def state(self):
        return self.content.state()

    def __getattr__(self, attribute):
        return getattr(self.content.instance, attribute)

class ContextWrappable(object):
    contextclass = ContentContext

    def ctx(self, *args, **kwargs):
        """ return a context wrapped version of self """
        return self.contextclass(self, *args, **kwargs)
