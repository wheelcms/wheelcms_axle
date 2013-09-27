from django import forms
from userena.forms import EditProfileForm
from django.utils.translation import ugettext as _

class UserenaDetailsFormExtra(EditProfileForm):
    twitter = forms.CharField(label=_(u'Twitter'), required=False)
    google = forms.CharField(label=_(u'Google+'), required=False)
    linkedin = forms.CharField(label=_(u'LinkedIn'), required=False)

    def __init__(self, *args, **kw):
        super(UserenaDetailsFormExtra, self).__init__(*args, **kw)

