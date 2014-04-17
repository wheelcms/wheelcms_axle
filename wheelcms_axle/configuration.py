import operator

from django import forms
from django.core.urlresolvers import reverse

from two.ol.base import applyrequest

from two.ol.base import FormHandler
from wheelcms_axle.models import Configuration
from wheelcms_axle.base import WheelHandlerMixin

from .themes import theme_registry
from .registries.configuration import configuration_registry

from wheelcms_axle import auth

from wheelcms_axle.spoke import Spoke

import wheelcms_axle.permissions as p

class BaseConfigurationHandler(object):
    id = ""
    label = ""
    model = None
    form = None

    def view(self, handler, instance):
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
        handler.context['tabs'] = handler.construct_tabs(self.id)
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

        for section in [default] + sorted(configs.values(),
                                          key=operator.attrgetter("label")):
            instance = None
            form = None
            selected = False

            if section.id == config:
                if section.id and section.model:
                    try:
                        instance = getattr(baseconf, section.id).get()
                    except section.model.DoesNotExist:
                        pass
                else:
                    instance = baseconf
                if section.form:
                    form=section.form(instance=instance)
                selected = True
            tabs.append(dict(label=section.label,
                             related=section.id,
                             form=form,
                             selected=selected))

        return tabs

    def get_instance(self, config):
        instance = Configuration.config()
        klass = configuration_registry.get(config)

        if klass.model and config:
            try:
                instance = getattr(instance, config).get()
            except klass.model.DoesNotExist:
                instance = klass.model(main=instance)
                instance.save()
        return instance

    # @require(p.modify_settings)
    @applyrequest
    def index(self, config="", action=""):
        ## XXX Decorate this!
        if not auth.has_access(self.request, Spoke, None, p.modify_settings):
            return self.forbidden()

        instance = self.get_instance(config)
        klass = configuration_registry.get(config)
        self.context['tabs'] = self.construct_tabs(klass.id)

        k = klass()

        if action:
            action_handler = getattr(k, action, None)
            if action_handler and getattr(action_handler, 'action', False):
                return getattr(k, action)(self, instance)

        return k.view(self, instance)


    #@require(p.modify_settings)
    @applyrequest
    def process(self, config="", action=""):
        ## XXX Decorate this!
        if not auth.has_access(self.request, Spoke, None, p.modify_settings):
            return self.forbidden()
        instance = self.get_instance(config)

        klass = configuration_registry.get(config)
        self.context['tabs'] = self.construct_tabs(klass.id)

        k = klass()

        if action:
            action_handler = getattr(k, action, None)
            if action_handler and getattr(action_handler, 'action', False):
                return getattr(k, action)(self, instance)

        return klass().process(self, instance)


configuration_registry.register("", "Default", Configuration, ConfigurationForm)
