from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1
from wheelcms_axle.forms import formfactory

from .fixtures import multilang_ENNL, root

from .utils import MockedQueryDict

import pytest

@pytest.mark.usefixtures("multilang_ENNL")
class TestContentCreate(object):
    type = Type1

    def test_success(self, client):
        """ simple case where create succeeds """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world",
                                            language="en"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"

    def test_title_missing(self, client):
        """ title is missing """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(slug="world",
                                                       language="en"))
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_slug_invalid(self, client):
        """ invalid characters in slug """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world$", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_slug_used(self, client):
        """ slug already exists in parent """
        root = Node.root()
        root.add('world')
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_tags(self, client):
        """ test tag suport on content """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                                       slug="world",
                                                       tags="hello, world",
                                                       language="en"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"
        assert "hello" in tp1.tags.values_list("name", flat=True)
        assert "world" in tp1.tags.values_list("name", flat=True)

    def test_available_languages(self, client):
        root = Node.root()
        form = formfactory(Type1)(parent=root,node=root)

        assert set((x[0] for x in form.fields['language'].choices)) == \
               set(('en', 'nl', 'any'))

    def test_allowed_subcontent_empty(self, client):
        """
            If no subcontent is explicitly selected, allowed should
            be saved as NULL which will be interpreted as "use class defaults"
        """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                                       slug="world",
                                                       tags="hello, world",
                                                       language="en",
                                                       allowed=[]))
        assert form.is_valid()
        tp1 = form.save()
        assert tp1.allowed is None

    def test_allowed_subcontent_selection(self, client):
        """
            If an explicit selection is made, this selection should
            be saved as comma separated string
        """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(
                                     title="hello",
                                     slug="world",
                                     tags="hello, world",
                                     language="en",
                                     allowed=["tests.type1", "tests.type2"]))
        assert form.is_valid()
        tp1 = form.save()
        assert tp1.allowed == "tests.type1,tests.type2"

    def test_allowed_subcontent_nosubcontent(self, client):
        """
            If the "no_sucontent" checkbox is checked, no subcontent
            is allowed, which is saved as an empty string (not NULL!)

            Regardless of an "allowed" selection!
        """
        root = Node.root()
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(
                                     title="hello",
                                     slug="world",
                                     tags="hello, world",
                                     language="en",
                                     allowed=["tests.type1", "tests.type2"],
                                     no_subcontent=True))
        assert form.is_valid()
        tp1 = form.save()
        assert tp1.allowed == ""

    def test_allowed_subcontent_selection_existing(self, client, root):
        """
            Verify the selection is correctly initialized from a
            comma separated string
        """
        t = Type1(node=root, title="test", language="en",
                  allowed="tests.type1,tests.type2").save()
        form = formfactory(Type1)(parent=root, instance=t)
        assert set(form['allowed'].value()) == \
               set(('tests.type1', 'tests.type2'))

@pytest.mark.usefixtures("multilang_ENNL")
class TestContentUpdate(object):
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
