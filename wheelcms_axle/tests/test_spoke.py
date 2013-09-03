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
from wheelcms_axle.content import TypeRegistry, type_registry
from wheelcms_axle.templates import TemplateRegistry, template_registry
from wheelcms_axle.spoke import Spoke

DEFAULT = "wheelcms_axle/content_view.html"

filedata = SimpleUploadedFile("foo.png",
           'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
           '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

filedata2 = SimpleUploadedFile("foo2.png",
           'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
           '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02E\x01\x00;')

class BaseLocalRegistry(object):
    """
        Make sure registries are local to the test
    """
    type = None
    types = ()

    def setup(self):
        """ override the global registry """
        self.registry = TypeRegistry()
        type_registry.set(self.registry)
        if self.type:
            self.registry.register(self.type)
        for type in self.types:
            self.registry.register(type)

class BaseSpokeTest(BaseLocalRegistry):
    """
        Basic spoke testing
    """
    type = None

    @classproperty
    def typename(cls):
        return cls.type.model.get_name()

    def test_name(self, client):
        """
            Name generation
        """
        model = self.type.model()
        model.save()
        spoke = self.type(model)

        assert spoke.name() == self.typename

    def test_fields(self, client):
        """
            Test the fields() method that iterates over the
            model instances fields
        """
        model = self.type.model()
        model.save()
        spoke = self.type(model)
        fields = dict(spoke.fields())

        assert 'title' in fields

        return fields  ## for additional tests


class BaseSpokeTemplateTest(BaseLocalRegistry):
    """
        Test template related validation/behaviour
    """
    def valid_data(self):
        """ return formdata required for validation to succeed """
        return {}

    def valid_files(self):
        """ return formdata files required for validation to succeed """
        return {}

    def setup(self):
        """ create clean local registries, make sure it's used globally """
        super(BaseSpokeTemplateTest, self).setup()

        self.reg = TemplateRegistry()
        template_registry.set(self.reg)

        self.root = Node.root()

    def test_empty(self, client):
        """ An empty registry """
        form = self.type.form(parent=self.root)
        assert 'template' not in form.fields
        model = self.type.model()
        model.save()
        assert self.type(model).view_template() == DEFAULT

    def test_single(self, client):
        """ An single template registered """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        form = self.type.form(parent=self.root)
        assert 'template' in form.fields
        assert form.fields['template'].choices == [('foo/bar', 'foo bar')]
        model = self.type.model()
        model.save()
        assert self.type(model).view_template() == 'foo/bar'

    def test_default(self, client):
        """ If there's a default, it should be used """
        model = self.type.model()
        model.save()
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        self.reg.register(self.type, "foo/bar2", "foo bar", default=True)
        self.reg.register(self.type, "foo/bar3", "foo bar", default=False)
        assert self.type(model).view_template() == "foo/bar2"

    def test_explicit(self, client):
        """ unless there's an explicit other selection """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        self.reg.register(self.type, "foo/bar2", "foo bar", default=True)
        self.reg.register(self.type, "foo/bar3", "foo bar", default=False)
        model = self.type.model(template="foo/bar3")
        model.save()
        assert self.type(model).view_template() == "foo/bar3"

    def test_form_excluded(self, client):
        """ verify certain fields are excluded from the form """
        form = self.type.form(parent=self.root, data={'template':"bar/foo"})
        assert 'node' not in form.fields
        assert 'meta_type' not in form.fields
        assert 'owner' not in form.fields
        assert 'classess' not in form.fields

    def test_form_validation_fail(self, client):
        """ Only registered templates are allowed """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        form = self.type.form(parent=self.root, data={'template':"bar/foo",
                                                      'language':'en'})
        assert not form.is_valid()
        assert 'template' in form.errors

    def test_form_validation_language(self, client):
        """ language is required """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        data = self.valid_data()
        data['template'] = 'foo/bar'
        form = self.type.form(parent=self.root, data=data)
        assert not form.is_valid()
        assert 'language' in form.errors

    def test_form_validation_success(self, client):
        """ In the end it should succeed """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        self.reg.register(self.type, "foo/bar2", "foo bar", default=True)
        self.reg.register(self.type, "foo/bar3", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['slug'] = 's'
        data['title'] = 't'
        data['template'] = 'foo/bar3'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['template'] == "foo/bar3"

    def test_slug_exists(self, client):
        """ a slug has been chosen that's already in use """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data()
        data['slug'] = 'foo'
        data['title'] = 't'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert not form.is_valid()
        assert 'slug' in form.errors
        assert form.errors['slug'].pop() == 'Name in use'  ## fragile

    def test_slug_generate(self, client):
        """ test slug generation """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'Hello World'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()

    def test_slug_generate_dashes(self, client):
        """ test slug generation """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'foo -- bar  -  cccc'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == "foo-bar-cccc"

    def test_slug_generate_stopwords(self, client):
        """ test slug generation """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'a world the are'
        data['template'] = 'foo/bar'
        data['language'] = 'en' ## use english stopwords

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == "world"

    def test_slug_generate_stopwords_empty(self, client):
        """ test slug generation - only stopwords """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'are'
        data['template'] = 'foo/bar'
        data['language'] = 'en' ## use english stopwords

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug']

    def test_slug_generate_stopwords_empty_dashes(self, client):
        """ test slug generation - only stopwords """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'are - a - they'
        data['template'] = 'foo/bar'
        data['language'] = 'en' ## use english stopwords

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug']

    def test_slug_generate_complex(self, client):
        """ test slug generation """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['title'] = 'Hello World, What\'s up?'
        data['slug'] = ''
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'hello-world-what-s-up'

    def test_slug_generate_conflict(self, client):
        """ slug generation should not create duplicate slugs """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data()
        data['slug'] = ''
        data['title'] = 'foo'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files())

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo1'

    def test_slug_reserved(self, client):
        """
            An explicitly specified slug that matches a reserved word
            should result in a validation error
        """
        p = Node.root()
        data = self.valid_data()
        data['slug'] = 'foobar'
        data['title'] = 'foo'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

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
        data = self.valid_data()
        data['slug'] = 'foobar1'
        data['title'] = 'foo'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
            reserved=["foobar"])

        assert form.is_valid()

    def test_slug_generate_reserved(self, client):
        """ slug generation should not create reserved names """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        data = self.valid_data()
        data['slug'] = ''
        data['title'] = 'foo'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
                              reserved=["foo"])

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo1'

    def test_slug_generate_reserved_existing(self, client):
        """ slug generation should not create reserved names or existing
            names, combined """
        self.reg.register(self.type, "foo/bar", "foo bar", default=False)
        p = Node.root()
        p.add('foo')
        data = self.valid_data()
        data['slug'] = ''
        data['title'] = 'foo'
        data['template'] = 'foo/bar'
        data['language'] = 'en'

        form = self.type.form(parent=p, data=data, files=self.valid_files(),
                              reserved=["foo1"])

        assert form.is_valid()
        assert form.cleaned_data['slug'] == 'foo2'

    def test_context(self, client):
        """ a context method can be stored in the registry """
        def ctx(ins):
            return dict(a="1")

        self.reg.register(self.type, "foo/bar", "foo bar",
                          default=False, context=ctx)

        context_method = self.reg.context.get((self.type, "foo/bar"))
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

class TestImplicitAddition(object):
    """
        Test implicit/explicit addition of children
    """
    def setup(self):
        """ local registry, install it globally """
        self.registry = TypeRegistry()
        type_registry.set(self.registry)

    def test_explicit(self, client):
        """ Simple case, no restrictions """
        class T1(ModellessSpoke):
            implicit_add = True  ## default

        class T2(ModellessSpoke):
            children = None

        self.registry.register(T1)
        self.registry.register(T2)

        assert T1 in T2.addable_children()

    def test_non_implicit(self, client):
        """ T1 cannot be added explicitly """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            children = None

        self.registry.register(T1)
        self.registry.register(T2)

        assert T1 not in T2.addable_children()

    def test_non_implicit_but_children(self, client):
        """ T1 cannot be added explicitly but is in T2's children """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            children = (T1, )

        self.registry.register(T1)
        self.registry.register(T2)

        assert T1 in T2.addable_children()

    def test_non_implicit_but_exp_children(self, client):
        """ T1 cannot be added explicitly but is in T2's explicit
            children """
        class T1(ModellessSpoke):
            implicit_add = False

        class T2(ModellessSpoke):
            explicit_children = (T1, )

        self.registry.register(T1)
        self.registry.register(T2)

        assert T1 in T2.addable_children()

class TestFileContent(BaseLocalRegistry):
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

class TestImageContent(BaseLocalRegistry):
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
