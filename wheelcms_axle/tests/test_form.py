import mock
import pytest

from django import forms

from wheelcms_axle.forms import ParentField, BaseForm, AngularForm
from .models import Type1

class TestParentField(object):
    def test_init(self):
        something = mock.Mock()
        f = ParentField(something)
        assert f.parent is None
        assert f.parenttype == something

    def test_clean_noparent(self):
        something = mock.Mock()
        f = ParentField(something)
        with pytest.raises(forms.ValidationError):
            f.clean("")

    def test_clean_mistype(self):
        f = ParentField(str)
        f.parent = mock.MagicMock()
        with pytest.raises(forms.ValidationError):
            f.clean("")

    def test_clean(self):
        class DummyContent(object):
            def content(self):
                return "content"

        f = ParentField(str)
        f.parent = DummyContent()

        assert f.clean("") == "content"

    def test_forminit(self, client):
        """ A ParentField should receive its parent form the form """
        ## unfortunately, BaseForm depends on lots of stuff, including
        ## database access
        class Form(BaseForm):
            class Meta:
                model = Type1

            field = ParentField()

        parent = mock.MagicMock()
        form = Form(parent)

        assert form.fields['field'].parent == parent

class TestAngularForm(object):
    def test_no_namespace(self):
        class TestForm(AngularForm):
            field = forms.CharField()

        f = TestForm()
        assert f.fields['field'].widget.attrs.get('ng-model') == 'field'

    def test_with_namespace(self):
        class TestForm(AngularForm):
            ng_ns = "test.ns"
            field = forms.CharField()

        f = TestForm()
        assert f.fields['field'].widget.attrs.get('ng-model') == 'test.ns.field'

    def test_with_namespace_multiple(self):
        class TestForm(AngularForm):
            ng_ns = "test.ns"

            field1 = forms.CharField()
            field2 = forms.CharField()

        f = TestForm()
        assert f.fields['field1'].widget.attrs.get('ng-model') == \
               'test.ns.field1'
        assert f.fields['field2'].widget.attrs.get('ng-model') ==  \
               'test.ns.field2'
