import re
import mimetypes

from django import forms
from wheelcms_axle.models import Node

from wheelcms_axle.models import type_registry, Configuration
from wheelcms_axle.templates import template_registry

from tinymce.widgets import TinyMCE as BaseTinyMCE

from taggit.utils import parse_tags

class TinyMCE(BaseTinyMCE):
    def render(self, name, value, attrs=None):
        ## this will always overwrite content_css; modifiying it will
        ## be a problem when the theme changes.
        self.mce_attrs['content_css'] = self.theme_css()
        return super(TinyMCE, self).render(name, value, attrs)

    def theme_css(self):
        theme = Configuration.config().themeinfo()

        return ",".join(theme.css_resources())

class TagWidget(forms.TextInput):
    """ taggit's own TagWidget finds it necessary for unknown reasons
        to "quote" tags containing a space, something that our tagsManager
        plugin can't handle wel.
    """
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, basestring):
            value = ",".join(o.tag.name for o in value.select_related("tag"))

        return super(TagWidget, self).render(name, value, attrs)

class BaseForm(forms.ModelForm):
    light = False  ## by default it's not a light form

    class Meta:
        exclude = ["node", "meta_type", "owner", "classes"]

    initial_advanced_fields =  ["created", "modified", "publication",
                                "expire", "state", "template", "navigation",
                                "important"]

    def content_fields(self):
        return set(self.fields) - set(self.advanced_fields)

    slug = forms.Field(required=False, help_text="A slug determines the url "
          "of the content. You can leave this empty to auto-generate a slug.")

    tags = forms.Field(required=False, help_text="Zero or more tags. Create a tag by ending with a comma or enter", widget=TagWidget())

    # just an experiment, to have a required field in the advanced section
    # important = forms.Field(required=True)

    def __init__(self, parent, attach=False, enlarge=True, reserved=(),
                 *args, **kwargs):
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
        self.reserved = reserved
        self.advanced_fields = self.initial_advanced_fields

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

        if enlarge:
            for enlargable_field in self.fields.values():
                self.enlarge_field(enlargable_field)

        ## make the description textarea a bit smaller
        if 'description' in self.fields:
            self.fields['description'].widget.attrs['rows'] = 4
        
        if 'tags' in self.fields:
            self.fields['tags'].widget.attrs['class'] = "tagManager"
            self.fields['tags'].required = False

        for e in type_registry.extenders(self.Meta.model):
            e.extend_form(self, *args, **kwargs)

        #from wheelcms_categories.models import fix_form
        # 
        #fix_form(self, *args, **kwargs)


    def enlarge_field(self, field):
        field.widget.attrs['class'] = 'input-xxlarge'

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

        # import pytest; pytest.set_trace()
        if not slug:
            slug = re.sub("[^%s]+" % Node.ALLOWED_CHARS, "-",
                          self.cleaned_data.get('title', '').lower()
                          )[:Node.MAX_PATHLEN].strip("-")
            try:
                existing = Node.objects.filter(path=parent_path
                                               + "/" + slug).get()
            except Node.DoesNotExist:
                existing = None

            base_slug = slug[:Node.MAX_PATHLEN-6] ## some space for counter
            count = 1
            while (existing and existing != self.instance.node) or \
                  (slug in self.reserved):
                slug = base_slug + str(count)
                try:
                    existing = Node.objects.filter(path=self.parent.path
                                                   + "/" + slug).get()
                except Node.DoesNotExist:
                    existing = None

                count += 1

        if slug in self.reserved:
            raise forms.ValidationError("This is a reserved name")

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

    def clean_tags(self):
        """ taggit's parse_tags behaves oddly when a single tag (no comma)
            is passed:

            (Pdb) print parse_tags("google io")
            [u'google', u'io']
            (Pdb) print parse_tags("google io,")
            [u'google io']

            We always only want to split on comma. To enforce this,
            simply had a comma before calling parse_tags
        """

        tags = self.data.get('tags', '')
        t = parse_tags(tags+",")
        return t

    def clean_template(self):
        template = self.data.get('template')
        if not template:
            return ""

        if not template_registry.valid_for_model(self._meta.model, template):
            raise forms.ValidationError("Invalid template")
        return template

    def save(self, commit=True):
        i = super(BaseForm, self).save(commit=False)

        for e in type_registry.extenders(self.Meta.model):
            e.extend_save(self, i, commit)

        if commit:
            i.save()
            self.save_m2m()

        return i


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
    islight = light  ## redefine as local for Form's closure

    class Form(base):
        light = islight

        class Meta(base.Meta):
            if light:
                fields = ('title', 'state', 'storage')

        content_type = forms.ChoiceField(
                        choices=(('', 'detect type'),) +
                                 tuple((x, x) for x in
                                       sorted(mimetypes.types_map.values())
                                ), required=False)


        def __init__(self, *args, **kw):
            """ make the title field not required """
            super(Form, self).__init__(enlarge=False, *args, **kw)
            self.fields['title'].required = False
            self.fields['storage'].label = "Upload"
            if light:
                self.fields['slug'].widget = forms.HiddenInput()
                self.fields['template'].widget = forms.HiddenInput()

            if 'tags' in self.fields:
                del self.fields['tags']  ## not tagselection

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

