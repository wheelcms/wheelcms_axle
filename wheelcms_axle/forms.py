import re
import mimetypes

from django import forms
from wheelcms_axle.models import Node

from wheelcms_axle.models import type_registry
from wheelcms_axle.templates import template_registry


class BaseForm(forms.ModelForm):
    class Meta:
        exclude = ["node", "meta_type", "owner", "classes"]

    slug = forms.Field(required=False)

    def __init__(self, parent, attach=False, *args, **kwargs):
        """
            Django will put the extra slug field at the bottom, below
            all model fields. I want it just after the title field
        """
        super(BaseForm, self).__init__(*args, **kwargs)
        slug = self.fields.pop('slug')
        titlepos = self.fields.keyOrder.index('title')
        self.fields.insert(titlepos+1, 'slug', slug)
        self.parent = parent
        self.attach = attach
        if attach:
            self.fields.pop('slug')

        templates = template_registry.get(self._meta.model, [])
        if templates:
            self.fields['template'] = forms.ChoiceField(choices=templates,
                                                        required=False)
        else:
            self.fields.pop('template')  ## will default to content_view

        self.fields['state'] = forms.ChoiceField(choices=self.workflow_choices(),
                                                 initial=self.workflow_default(),
                                                 required=False)
        if self.instance and self.instance.node and self.instance.node.isroot():
            self.fields.pop("slug")

    def workflow_choices(self):
        """
            return valid choices. Is actually context dependend (not all states
            can be reached from a given state)
        """
        spoke = type_registry.get(self._meta.model.get_name())
        return spoke.workflowclass.states

    def workflow_default(self):
        """
            Return default state for active workflow
        """
        spoke = type_registry.get(self._meta.model.get_name())
        return spoke.workflowclass.default

    def clean_slug(self):
        if self.attach:
            return

        slug = self.data.get('slug', '').strip().lower()

        parent_path = self.parent.path

        if not slug:
            slug = re.sub("[^%s]+" % Node.ALLOWED_CHARS, "-",
                          self.cleaned_data.get('title', '').lower()
                          )[:Node.MAX_PATHLEN].strip("-")
            try:
                existing = Node.objects.filter(path=parent_path
                                               + "/" + slug).get()
                base_slug = slug[:Node.MAX_PATHLEN-6] ## some space for counter
                count = 1
                while existing and existing != self.instance.node:
                    slug = base_slug + str(count)
                    existing = Node.objects.filter(path=self.parent.path
                                                   + "/" + slug).get()
                    count += 1

            except Node.DoesNotExist:
                pass

        if not Node.validpathre.match(slug):
            raise forms.ValidationError("Only numbers, letters, _-")
        try:
            existing = Node.objects.filter(path=parent_path + "/" + slug
                                          ).get()
            if existing != self.instance.node:
                raise forms.ValidationError("Name in use")
        except Node.DoesNotExist:
            pass

        return slug

    def clean_template(self):
        template = self.data.get('template')
        if not template:
            return ""

        if not template_registry.valid_for_model(self._meta.model, template):
            raise forms.ValidationError("Invalid template")
        return template


def formfactory(type):
    class Form(BaseForm):
        class Meta(BaseForm.Meta):
            model = type
            exclude = BaseForm.Meta.exclude + ["created", "modified"]
    return Form

def FileFormfactory(type, light=False):
    """
        Provide a form that has an optional title field. If left
        unspecified, take the filename from the uploaded file in stead.
    """
    base = formfactory(type)

    class Form(base):
        class Meta(base.Meta):
            if light:
                fields = [ 'title', 'state', 'storage' ]

        content_type = forms.ChoiceField(
                        choices=(('', 'detect type'),) +
                                 tuple((x, x) for x in
                                       sorted(mimetypes.types_map.values())
                                ), required=False)


        def __init__(self, *args, **kw):
            """ make the title field not required """
            super(Form, self).__init__(*args, **kw)
            self.fields['title'].required = False
            if light:
                self.fields['slug'].widget = forms.HiddenInput()
                self.fields['template'].widget = forms.HiddenInput()

        def clean_title(self):
            """ generate title based on filename if necessary """
            title = self.data.get('title', '').strip()
            try:
              if not title:
                  title = self.files.get('storage').name
            except AttributeError:
                ## there is no file upload. This will cause validation
                ## to fail at a later stage but it shouldn't produce
                ## errors now
                title = ''
            return title
    return Form

