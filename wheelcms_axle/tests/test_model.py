"""
    Model specific stuff
"""
from wheelcms_spokes.file import File
from wheelcms_spokes.image import Image
from wheelcms_axle.tests.models import TestFile, TestImage
from wheelcms_axle.models import FileContent, ImageContent, ContentClass

from django.core.files.uploadedfile import SimpleUploadedFile

filedata = SimpleUploadedFile("foo.png",
           'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
           '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

class TestFileContent(object):
    """ verify File based content can be found in a single query """
    def test_combined(self, client):
        """ create a file, testfile and image, query the base and find all """
        file1, _ = File.objects.get_or_create(storage=filedata)
        file2, _ = Image.objects.get_or_create(storage=filedata)
        file3, _ = TestFile.objects.get_or_create(storage=filedata)

        files = ContentClass.objects.get(
                       name=FileContent.FILECLASS).content.all()
        assert set(x.content() for x in files) == set((file1, file2, file3))

    def test_combined_manager(self, client):
        """ create a file, testfile and image and find them using the
            instances manager """
        file1, _ = File.objects.get_or_create(storage=filedata)
        file2, _ = Image.objects.get_or_create(storage=filedata)
        file3, _ = TestFile.objects.get_or_create(storage=filedata)

        files = FileContent.instances.all()
        assert set(x.content() for x in files) == set((file1, file2, file3))

class TestImageContent(object):
    """ verify Image based content can be found in a single query """
    def test_combined(self, client):
        """ create a file, testfile and image, query the base and find all """
        file1, _ = File.objects.get_or_create(storage=filedata)
        file2, _ = Image.objects.get_or_create(storage=filedata)
        file3, _ = TestImage.objects.get_or_create(storage=filedata)

        files = ContentClass.objects.get(
                       name=ImageContent.IMAGECLASS).content.all()
        assert set(x.content() for x in files) == set((file2, file3))

    def test_combined_manager(self, client):
        """ create a file, testfile and image and find them using the
            instances manager """
        file1, _ = File.objects.get_or_create(storage=filedata)
        file2, _ = Image.objects.get_or_create(storage=filedata)
        file3, _ = TestImage.objects.get_or_create(storage=filedata)

        files = ImageContent.instances.all()
        assert set(x.content() for x in files) == set((file2, file3))
