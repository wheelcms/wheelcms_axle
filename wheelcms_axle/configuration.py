import operator

from django import forms
from django.core.urlresolvers import reverse

from two.ol.base import applyrequest

from two.ol.base import FormHandler
from wheelcms_axle.models import Configuration
from wheelcms_axle.base import WheelHandlerMixin

from .themes import theme_registry
from .registries.configuration import configuration_registry

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
        default = [("", configs.pop(""))]

        configs = default + sorted(configs.iteritems(), key=operator.itemgetter(1))
        for (related, (label, model, formclass)) in configs:
            instance = None
            form = None
            selected = False

            if related == config:
                if related:
                    try:
                        instance = getattr(baseconf, related).get()
                    except model.DoesNotExist:
                        pass
                else:
                    instance = baseconf
                form=formclass(instance=instance)
                selected = True
            tabs.append(dict(label=label,
                             related=related,
                             form=form,
                             selected=selected))
        return tabs

    @applyrequest
    def index(self, config=""):
        if not self.hasaccess():
            return self.forbidden()

        self.context['tabs'] = self.construct_tabs(config)
        ## set redirect_to
        return self.template("wheelcms_axle/configuration.html")

    @applyrequest
    def process(self, config=""):
        instance = Configuration.config()
        (label, model, formclass) = configuration_registry.get(config)

        if config:
            try:
                instance = getattr(instance, config).get()
            except model.DoesNotExist:
                instance = model(main=instance)
                instance.save()

        self.context['form'] = form = \
                 formclass(self.request.POST, instance=instance)
        if form.is_valid():
            form.save()
            ## include hash, open tab
            return self.redirect(reverse('wheel_config'), config=config, success="Changes saved")
        self.context['tabs'] = self.construct_tabs(config)
        return self.template("wheelcms_axle/configuration.html")

configuration_registry.register("", "Default", Configuration, ConfigurationForm)
