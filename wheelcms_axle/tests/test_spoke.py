"""
    Model specific stuff
"""
from django.core.files.uploadedfile import SimpleUploadedFile

from two.ol.util import classproperty

from wheelcms_axle.tests.models import TestFile, TestImage
from wheelcms_axle.tests.models import OtherTestFile, OtherTestImage
from wheelcms_axle.tests.models import TestFileType, TestImageType
from wheelcms_axle.tests.models import OtherTestFileType, OtherTestImageType
from wheelcms_axle.tests.models import Type1Type
from wheelcms_axle.models import FileContent, ImageContent, ContentClass


from wheelcms_axle.node import Node
from wheelcms_axle.content import type_registry
from wheelcms_axle.templates import template_registry
from wheelcms_axle.spoke import Spoke

from .utils import MockedQueryDict, DummyContent

import pytest

DEFAULT = "wheelcms_axle/content_view.html"

filedata = SimpleUploadedFile("foo.png",
           'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
           '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

filedata2 = SimpleUploadedFile("foo2.png",
           'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
           '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02E\x01\x00;')

@pytest.mark.usefixtures("localtyperegistry")
class BaseSpokeTest(object):
    """
        Basic spoke testing
    """
    type = None

    def create_instance(self):
        return self.type.model()

    @classproperty
    def typename(cls):
        return cls.type.model.get_name()

    def test_equal_none(self, client):
        """
            A spoke is not equal to None
        """
        s = self.create_instance().spoke().save()
        assert not s == None

    def test_nonequal_none(self, client):
        """
            A spoke is not equal to None
        """
        s = self.create_instance().spoke().save()
        assert s != None

    def test_equal_self(self, client):
        """
            A spoke is equal to itself
        """
        s = self.create_instance().spoke().save()
        assert s == s

    def test_equal_multi_spokes(self, client):
        """
            Same instance, different spokes
        """
        i = self.create_instance().save()
        s1 = i.spoke()
        s2 = i.spoke()

        assert s1 == s2

    def test_notequal_multi_spokes(self, client):
        """
            Different spokes, different models
        """
        s1 = self.create_instance().spoke().save()
        s2 = self.create_instance().spoke().save()
        assert s1 != s2

    def test_name(self, client):
        """
            Name generation
        """
        model = self.create_instance()
        model.save()
        spoke = self.type(model)

        assert spoke.name() == self.typename

    def test_fields(self, client):
        """
            Test the fields() method that iterates over the
            model instances fields
        """
        model = self.create_instance()
        model.save()
        spoke = self.type(model)
        fields = dict(spoke.fields())

        assert 'title' in fields

        return fields  ## for additional tests

    def test_spoke_save(self, client):
        """
            A spoke can save its instance
        """
        M = self.type.model

        model = self.create_instance()
        spoke = self.type(model)
        spoke.save()
        assert M.objects.all()[0] == model


@pytest.mark.usefixtures("localtyperegistry", "localtemplateregistry")
class BaseSpokeTemplateTest(object):
    """
        Test template related validation/behaviour
    """
    def create_instance(self, **kw):
        return self.type.model(**kw)

    def valid_data(self, **kw):
        """ return formdata required for validation to succeed """
        return MockedQueryDict(**kw)

    def valid_files(self):
        """ return formdata files required for validation to succeed """
        return {}

    def test_empty(self, client, root):
        """ An empty registry """
        form = self.type.form(parent=root)
        assert 'template' not in form.fields
        model = self.create_instance()
        model.save()
        assert self.type(model).view_template() == DEFAULT

    def test_single(self, client, root):
        """ An single template registered """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        form = self.type.form(parent=root)
        assert 'template' in form.fields
        assert form.fields['template'].choices == [('foo/bar', 'foo bar')]
        model = self.create_instance()
        model.save()
        assert self.type(model).view_template() == 'foo/bar'

    def test_default(self, client):
        """ If there's a default, it should be used """
        model = self.create_instance()
        model.save()
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        template_registry.register(self.type, "foo/bar2", "foo bar", default=True)
        template_registry.register(self.type, "foo/bar3", "foo bar", default=False)
        assert self.type(model).view_template() == "foo/bar2"

    def test_explicit(self, client):
        """ unless there's an explicit other selection """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        template_registry.register(self.type, "foo/bar2", "foo bar", default=True)
        template_registry.register(self.type, "foo/bar3", "foo bar", default=False)
        model = self.create_instance(template="foo/bar3")
        model.save()
        assert self.type(model).view_template() == "foo/bar3"

    def test_form_excluded(self, client, root):
        """ verify certain fields are excluded from the form """
        form = self.type.form(parent=root, data={'template':"bar/foo"})
        assert 'node' not in form.fields
        assert 'meta_type' not in form.fields
        assert 'owner' not in form.fields
        assert 'classess' not in form.fields

    def test_form_validation_fail(self, client, root):
        """ Only registered templates are allowed """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        form = self.type.form(parent=root,
                              data=self.valid_data(template="bar/foo", language="en"))
        assert not form.is_valid()
        assert 'template' in form.errors

    def test_form_validation_language(self, client, root):
        """ language is required """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        data = self.valid_data(template="foo/bar")
        form = self.type.form(parent=root, data=data)
        assert not form.is_valid()
        assert 'language' in form.errors

    def test_form_validation_success(self, client):
        """ In the end it should succeed """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        template_registry.register(self.type, "foo/bar2", "foo bar", default=True)
        template_registry.register(self.type, "foo/bar3", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(slug="s", title="t", template="foo/bar3", language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['template'] == "foo/bar3"

    def test_slug_exists(self, client):
        """ a slug has been chosen that's already in use """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data(slug="foo", title="t", template="foo/bar", language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert not form.is_valid()
        assert 'slug' in form.errors
        assert form.errors['slug'].pop() == 'Name in use'  ## fragile

    def test_slug_generate(self, client):
        """ test slug generation """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(title="Hello World", template="foo/bar", language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()

    def test_slug_generate_dashes(self, client):
        """ test slug generation """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(title='foo -- bar  -  cccc', template='foo/bar',
                               language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == "foo-bar-cccc"

    def test_slug_generate_stopwords(self, client):
        """ test slug generation """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(title='a world the are', template='foo/bar',
                               language='en') ## use english stopwords

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"

    def test_slug_generate_stopwords_empty(self, client):
        """ test slug generation - only stopwords """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        ## use english stopwords
        data = self.valid_data(title="are", template="foo/bar", language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug']

    def test_slug_generate_stopwords_empty_dashes(self, client):
        """ test slug generation - only stopwords """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        ## use english stopwords
        data = self.valid_data(title="are - a - they", template="foo/bar", language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug']

    def test_slug_generate_complex(self, client):
        """ test slug generation """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(title='Hello World, What\'s up?',
                               slug='',
                               template='foo/bar',
                               language='en')

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'hello-world-what-s-up'

    def test_slug_generate_conflict(self, client):
        """ slug generation should not create duplicate slugs """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data(slug="", title="foo", template="foo/bar",
                               language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo1'

    def test_slug_reserved(self, client):
        """
            An explicitly specified slug that matches a reserved word
            should result in a validation error
        """
        p = Node.root()
        data = self.valid_data(slug="foobar", title="foo", template="foo/bar",
                               language="en")

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
            reserved=["foobar"])

        assert not form.is_valid()
        assert 'slug' in form.errors
        assert form.errors['slug'].pop() == 'This is a reserved name'  ## fragile

    def test_slug_notreserved(self, client):
        """
            An explicitly specified slug that doesn't match a reserved keyword
            should be accepted.
        """
        p = Node.root()
        data = self.valid_data(slug='foobar1',
                               title='foo',
                               template='foo/bar',
                               language='en')

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
            reserved=["foobar"])

        assert form.is_valid()

    def test_slug_generate_reserved(self, client):
        """ slug generation should not create reserved names """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data(slug='',
                               title='foo',
                               template='foo/bar',
                               language='en')

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
                              reserved=["foo"])

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo1'

    def test_slug_generate_reserved_existing(self, client):
        """ slug generation should not create reserved names or existing
            names, combined """
        template_registry.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data(slug='',
                               title='foo',
                               template='foo/bar',
                               language='en')

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
                              reserved=["foo1"])

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo2'

    def test_context(self, client):
        """ a context method can be stored in the registry """
        def ctx(ins):
            return dict(a="1")

        template_registry.register(self.type, "foo/bar", "foo bar",
                          default=False, context=ctx)

        context_method = template_registry.context.get((self.type, "foo/bar"))
        assert context_method
        assert context_method(None) == dict(a="1")

class TestType1Spoke(BaseSpokeTest):
    """
        Run base tests on test type 'type1'
    """
    type = Type1Type

    def test_fields(self, client):
        """ base tests + extra field """
        fields = super(TestType1Spoke, self).test_fields(client)
        assert 't1field' in fields


class TestType1SpokeTemplate(BaseSpokeTemplateTest):
    """
        Run base template tests on test type 'type1'
    """
    type = Type1Type


class ModellessSpoke(Spoke):
    """
        Handle the absence of a model
    """
    @classmethod
    def name(cls):
        return cls.__name__.lower()

class DummyModel(object):
    def __init__(self, allowed=None):
        self.allowed = allowed


@pytest.mark.usefixtures("localtyperegistry")
class TestImplicitAddition(object):
    """
        Test implicit/explicit addition of children
    """
    def test_explicit(self, client):
        """ Simple case, no restrictions """
        class T1(ModellessSpoke):
            implicit_add = True  ## default

        class T2(ModellessSpoke):
            children = None

        type_registry.register(T1)
        type_registry.register(T2)

        assert T1 in T2(DummyContent()).allowed_spokes()

    def test_non_implicit(self, client):
        """ T1 cannot be added explicitly """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            children = None

        type_registry.register(T1)
        type_registry.register(T2)

        assert T1 not in T2(DummyContent()).allowed_spokes()

    def test_non_implicit_but_children(self, client):
        """ T1 cannot be added explicitly but is in T2's children """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            children = (T1, )

        type_registry.register(T1)
        type_registry.register(T2)

        assert T1 in T2(DummyContent()).allowed_spokes()

    def test_non_implicit_but_exp_children(self, client):
        """ T1 cannot be added explicitly but is in T2's explicit
            children """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = (T1, )

        type_registry.register(T1)
        type_registry.register(T2)

        assert T1 in T2(DummyContent()).allowed_spokes()

    def test_config_nosub(self, client):
        """ instance has config, no subcontent """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = (T1, )

        type_registry.register(T1)
        type_registry.register(T2)

        assert T2(DummyContent(allowed="")).allowed_spokes() == ()

    def test_config_noconf(self, client):
        """ instance has config, no subcontent """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = (T1, )

        type_registry.register(T1)
        type_registry.register(T2)

        addable = T2(DummyContent(allowed=None)).allowed_spokes()
        assert T1 in addable
        assert T2 in addable

    def test_config_simpleconf(self, client):
        """ instance overrides default. In stead of all implicit content,
            only allow T1 """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = None

        type_registry.register(T1)
        type_registry.register(T2)

        assert T1 in T2(DummyContent(allowed="t1")).allowed_spokes()
        assert T2 not in T2(DummyContent(allowed="t1")).allowed_spokes()

    def test_config_spoke_allowed(self, client):
        """ Use the allowed() method on spokes """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = None

        type_registry.register(T1)
        type_registry.register(T2)

        t = T1(DummyContent())
        t.allow_spokes((T1, T2))

        assert T1 in t.allowed_spokes()
        assert T2 in t.allowed_spokes()

@pytest.mark.usefixtures("localtyperegistry")
class TestFileContent(object):
    """ verify File based content can be found in a single query """
    types = (OtherTestFileType, OtherTestImageType, TestFileType, TestImageType)

    def test_combined(self, client):
        """ create a file, testfile and image, query the base and find all """
        file1, _ = OtherTestFile.objects.get_or_create(storage=filedata)
        file2, _ = OtherTestImage.objects.get_or_create(storage=filedata)
        file3, _ = TestFile.objects.get_or_create(storage=filedata)

        files = ContentClass.objects.get(
                       name=FileContent.FILECLASS).content.all()
        assert set(x.content() for x in files) == set((file1, file2, file3))

    def test_combined_manager(self, client):
        """ create a file, testfile and image and find them using the
            instances manager """
        file1, _ = OtherTestFile.objects.get_or_create(storage=filedata)
        file2, _ = OtherTestImage.objects.get_or_create(storage=filedata)
        file3, _ = TestFile.objects.get_or_create(storage=filedata)

        files = FileContent.instances.all()
        assert set(x.content() for x in files) == set((file1, file2, file3))

@pytest.mark.usefixtures("localtyperegistry")
class TestImageContent(object):
    """ verify Image based content can be found in a single query """
    types = (OtherTestFileType, OtherTestImageType, TestFileType, TestImageType)

    def test_combined(self, client):
        """ create a file, testfile and image, query the base and find all """
        file1, _ = OtherTestFile.objects.get_or_create(storage=filedata)
        file2, _ = OtherTestImage.objects.get_or_create(storage=filedata)
        file3, _ = TestImage.objects.get_or_create(storage=filedata)

        files = ContentClass.objects.get(
                       name=ImageContent.IMAGECLASS).content.all()
        assert set(x.content() for x in files) == set((file2, file3))

    def test_combined_manager(self, client):
        """ create a file, testfile and image and find them using the
            instances manager """
        file1, _ = OtherTestFile.objects.get_or_create(storage=filedata)
        file2, _ = OtherTestImage.objects.get_or_create(storage=filedata)
        file3, _ = TestImage.objects.get_or_create(storage=filedata)

        files = ImageContent.instances.all()
        assert set(x.content() for x in files) == set((file2, file3))
