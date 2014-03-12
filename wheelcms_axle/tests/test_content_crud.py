from wheelcms_axle.models import Node
from wheelcms_axle.tests.models import Type1, Type1Type, Type2Type
from wheelcms_axle.forms import formfactory

from .fixtures import multilang_ENNL, root

from .utils import MockedQueryDict

import pytest

@pytest.mark.usefixtures("multilang_ENNL")
@pytest.mark.usefixtures("localtyperegistry")
class TestContentCreate(object):
    types = (Type1Type, Type2Type)

    def test_success(self, client, root):
        """ simple case where create succeeds """
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world",
                                            language="en"))
        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"
        tp1 = form.save()
        assert tp1.title == "hello"

    def test_title_missing(self, client, root):
        """ title is missing """
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(slug="world",
                                                       language="en"))
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_slug_invalid(self, client, root):
        """ invalid characters in slug """
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world$", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_slug_used(self, client, root):
        """ slug already exists in parent """
        root.add('world')
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                            slug="world", language="en"))
        assert not form.is_valid()
        assert 'slug' in form.errors

    def test_tags(self, client, root):
        """ test tag suport on content """
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

    def test_available_languages(self, client, root):
        form = formfactory(Type1)(parent=root,node=root)

        assert set((x[0] for x in form.fields['language'].choices)) == \
               set(('en', 'nl', 'any'))

    def test_allowed_subcontent_empty(self, client, root):
        """
            If no subcontent is explicitly selected, allowed should
            be saved as NULL which will be interpreted as "use class defaults"
        """
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(title="hello",
                                                       slug="world",
                                                       tags="hello, world",
                                                       language="en",
                                                       allowed=[]))
        assert form.is_valid()
        tp1 = form.save()
        assert tp1.allowed is None

    def test_allowed_subcontent_selection(self, client, root):
        """
            If an explicit selection is made, this selection should
            be saved as comma separated string
        """
        form = formfactory(Type1)(parent=root,
                                  data=MockedQueryDict(
                                     title="hello",
                                     slug="world",
                                     tags="hello, world",
                                     language="en",
                                     allowed=["tests.type1", "tests.type2"]))
        # import pytest;pytest.set_trace()
        assert form.is_valid()
        tp1 = form.save()
        assert tp1.allowed == "tests.type1,tests.type2"

    def test_allowed_subcontent_nosubcontent(self, client, root):
        """
            If the "no_sucontent" checkbox is checked, no subcontent
            is allowed, which is saved as an empty string (not NULL!)

            Regardless of an "allowed" selection!
        """
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

@pytest.mark.usefixtures("localtyperegistry")
@pytest.mark.usefixtures("multilang_ENNL")
class TestContentUpdate(object):
    type = Type1Type

    def test_available_languages(self, client, root):
        t = self.type.create(node=root, title="EN trans", language="en").save()

        form = formfactory(Type1)(parent=root,node=root)

        assert 'en' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))

    def test_available_languages_any(self, client, root):
        self.type.create(node=root, title="EN trans", language="en").save()
        self.type.create(node=root, title="ANY trans", language="any").save()

        form = formfactory(Type1)(parent=root,node=root)

        assert 'en' not in set((x[0] for x in form.fields['language'].choices))
        assert 'any' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))

    def test_available_languages_current(self, client, root):
        """ language can, of course, be selected if it's the content being
            editted """
        en = self.type.create(node=root, title="EN trans", language="en").save()
        any = self.type.create(node=root, title="ANY trans", language="any").save()

        form = formfactory(Type1)(parent=root,node=root, instance=en.instance)

        assert 'en' in set((x[0] for x in form.fields['language'].choices))
        assert 'any' not in set((x[0] for x in form.fields['language'].choices))
        assert 'nl' in set((x[0] for x in form.fields['language'].choices))
