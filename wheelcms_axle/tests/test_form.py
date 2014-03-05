import mock
import pytest

from django import forms

from wheelcms_axle.forms import ParentField, BaseForm
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
