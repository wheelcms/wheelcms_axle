from django.conf import settings

from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1
from wheelcms_axle.forms import formfactory

class BaseTest(object):
    def setup(self):
        settings.CONTENT_LANGUAGES = (('en', 'English'), ('nl', 'Nederlands'))
        settings.FALLBACK = 'en'

class TestContentCreate(BaseTest):
    type = Type1

    def test_success(self, client):
        """ simple case where create succeeds """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello", slug="world",
                                            language="en"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"

    def test_title_missing(self, client):
        """ title is missing """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(slug="world", language="en"))
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_slug_invalid(self, client):
        """ invalid characters in slug """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello",
                                            slug="world$", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_slug_used(self, client):
        """ slug already exists in parent """
        root = Node.root()
        root.add('world')
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello",
                                            slug="world", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_tags(self, client):
        """ test tag suport on content """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=dict(title="hello", slug="world", tags="hello, world", language="en"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"
        assert "hello" in tp1.tags.values_list("name", flat=True)
        assert "world" in tp1.tags.values_list("name", flat=True)

    def test_available_languages(self, client):
        root = Node.root()
        form = formfactory(Type1)(parent=root,node=root)

        assert set((x[0] for x in form.fields['language'].choices)) == set(('en', 'nl', 'any'))

class TestContentUpdate(BaseTest):
    type = Type1

    def test_available_languages(self, client):
        root = Node.root()
        t = self.type(node=root, title="EN trans", language="en").save()

        form = formfactory(Type1)(parent=root,node=root)

        assert 'en' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))

    def test_available_languages_any(self, client):
        root = Node.root()
        self.type(node=root, title="EN trans", language="en").save()
        self.type(node=root, title="ANY trans", language="any").save()

        form = formfactory(Type1)(parent=root,node=root)

        assert 'en' not in set((x[0] for x in form.fields['language'].choices))
        assert 'any' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))

    def test_available_languages_current(self, client):
        """ language can, of course, be selected if it's the content being
            editted """
        root = Node.root()
        en = self.type(node=root, title="EN trans", language="en").save()
        any = self.type(node=root, title="ANY trans", language="any").save()

        form = formfactory(Type1)(parent=root,node=root, instance=en)

        assert 'en' in set((x[0] for x in form.fields['language'].choices))
        assert 'any' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))
