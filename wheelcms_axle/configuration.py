import operator

from django import forms
from django.core.urlresolvers import reverse

from two.ol.base import applyrequest

from two.ol.base import FormHandler
from wheelcms_axle.models import Configuration
from wheelcms_axle.base import WheelHandlerMixin

from .themes import theme_registry
from .registries.configuration import configuration_registry

class BaseConfigurationHandler(object):
    id = ""
    label = ""
    model = None
    form = None

    def view(self, handler):
        handler.context['tabs'] = handler.construct_tabs(self.id)
        ## set redirect_to
        return handler.template("wheelcms_axle/configuration.html")

    def process(self, handler, instance):
        handler.context['form'] = form = \
                 self.form(handler.request.POST, instance=instance)
        if form.is_valid():
            form.save()
            ## include hash, open tab
            return handler.redirect(reverse('wheel_config'), config=self.id, success="Changes saved")
        handler.context['tabs'] = self.construct_tabs(self.id)
        return handler.template("wheelcms_axle/configuration.html")

class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = Configuration

    def __init__(self, *args, **kw):
        super(ConfigurationForm, self).__init__(*args, **kw)
        self.fields['theme'].choices = ((x.id, x.name) for x in theme_registry)

    theme = forms.ChoiceField()


class ConfigurationHandler(FormHandler, WheelHandlerMixin):
    def construct_tabs(self, config):
        baseconf = Configuration.config()
        tabs = []

        ## Sort by label, but default (key="") always goes first
        configs = configuration_registry.copy()
        default = configs.pop("")

        
        for section in [default] + sorted(configs.values(), key=operator.attrgetter("label")):
            instance = None
            form = None
            selected = False

            if section.id == config:
                if section.id:
                    try:
                        instance = getattr(baseconf, section.id).get()
                    except section.model.DoesNotExist:
                        pass
                else:
                    instance = baseconf
                form=section.form(instance=instance)
                selected = True
            tabs.append(dict(label=section.label,
                             related=section.id,
                             form=form,
                             selected=selected))

        return tabs

    @applyrequest
    def index(self, config=""):
        if not self.hasaccess():
            return self.forbidden()

        klass = configuration_registry.get(config)
        return klass().view(self)


    @applyrequest
    def process(self, config=""):
        instance = Configuration.config()
        klass = configuration_registry.get(config)

        if config:
            try:
                instance = getattr(instance, config).get()
            except klass.model.DoesNotExist:
                instance = klass.model(main=instance)
                instance.save()

        return klass().process(self, instance)


configuration_registry.register("", "Default", Configuration, ConfigurationForm)
