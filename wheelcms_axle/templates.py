from wheelcms_axle.registry import Registry

class TemplateRegistry(dict):
    def __init__(self, *arg, **kw):
        super(TemplateRegistry, self).__init__(*arg, **kw)
        self.defaults = {}
        self.context = {}

    def valid_for_model(self, model, template):
        return template in dict(self.get(model, []))

    def register(self, spoke, template, title, default=False, context=None):
        ## why key on spoke.model and not spoke? XXX
        ## because of the ModelForm?
        if spoke.model not in self:
            self[spoke.model] = []

        self[spoke.model].append((template, title))
        self.context[(spoke, template)] = context

        if default:
            self.defaults[spoke.model] = template

template_registry = Registry(TemplateRegistry())
