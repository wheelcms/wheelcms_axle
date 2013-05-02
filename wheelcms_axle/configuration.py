from django import forms
from django.core.urlresolvers import reverse


from two.ol.base import FormHandler
from wheelcms_axle.models import Configuration
from wheelcms_axle.base import WheelHandlerMixin

from .themes import theme_registry

class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = Configuration

    theme = forms.ChoiceField(choices=((x.id, x.name) for x in theme_registry))

class ConfigurationHandler(FormHandler, WheelHandlerMixin):
    def index(self):
        if not self.hasaccess():
            return self.forbidden()

        instance = Configuration.config()
        self.context['form'] = ConfigurationForm(instance=instance)
        ## set redirect_to
        return self.template("wheelcms_axle/configuration.html")

    def process(self):
        instance = Configuration.config()
        self.context['form'] = form = \
                 ConfigurationForm(self.request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return self.redirect(reverse('wheel_config'), success="Changes saved")
        return self.template("wheelcms_axle/configuration.html")
