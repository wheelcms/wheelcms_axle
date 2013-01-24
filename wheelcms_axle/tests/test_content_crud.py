from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1
from wheelcms_spokes.models import formfactory

class TestContentCreate(object):
    type = Type1

    def test_success(self, client):
        """ simple case where create succeeds """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello", slug="world"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"

    def test_title_missing(self, client):
        """ title is missing """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(slug="world"))
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_slug_invalid(self, client):
        """ invalid characters in slug """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello",
                                            slug="world$"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_slug_used(self, client):
        """ slug already exists in parent """
        root = Node.root()
        root.add('world')
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello",
                                            slug="world"))
        assert not form.is_valid()
        assert 'slug' in form.errors

