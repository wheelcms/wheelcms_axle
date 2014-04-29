class ContentContext(object):
    """
        A helper class that wraps content related stuff
        for easy access in templates
    """

    def __init__(self, content):
        self.content = content

    def title(self):
        return self.content.instance.title

    def url(self):
        return self.content.instance.get_absolute_url()


class ContextWrappable(object):
    contextclass = ContentContext

    def ctx(self, *args, **kwargs):
        return self.contextclass(self, *args, **kwargs)

