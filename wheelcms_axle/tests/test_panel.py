"""
    The panel method in the Main handler is responsible for filling the
    link/image selection/upload browser. It does a lot of stuff and needs
    some tests.
"""
from ..models import Node

from .models import Type1, Type1Type
from wheelcms_axle.tests.models import TestImage, TestImageType
from wheelcms_axle.tests.models import TestFile, TestFileType

from .test_handler import MainHandlerTestable, superuser_request

from django.core.files.uploadedfile import SimpleUploadedFile

storage = SimpleUploadedFile("foo.png", 
                             'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
                             '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

from .test_spoke import BaseLocalRegistry


class TestPanel(BaseLocalRegistry):
    """
        Test different panel invocation scenario's
    """
    types = (Type1Type, TestImageType, TestFileType)

    def test_unattached_root_link(self, client):
        """
            A single root with no content attached. Should allow
            upload of content
        """
        root = Node.root()
        request = superuser_request("/", method="GET")
        handler = MainHandlerTestable(request=request, instance=root)
        panels = handler.panels(path="", original="", mode="link")
        assert len(panels['panels']) == 2  ## bookmarks + 1 panel
        assert panels['path'] == root.get_absolute_url()

        crumbs = panels['crumbs']['context']['crumbs']
        assert len(crumbs) == 1
        assert crumbs[0]['path'] == root.get_absolute_url()

        ## inspect crumbs
        root_panel = panels['panels'][1]
        assert root_panel['context']['selectable']
        assert root_panel['context']['instance']['addables']

    def setup_root_children(self):
        """ setup some children """
        root = Node.root()
        i1 = Type1(node=root.add("type1")).save()
        i2 = TestImage(storage=storage, node=root.add("image")).save()
        i3 = TestFile(storage=storage, node=root.add("file")).save()

        return root, i1.node, i2.node, i3.node

    def test_root_children_link(self, client):
        """ panel in link mode, anything is selectable """
        root, t, i, f = self.setup_root_children()

        request = superuser_request("/", method="GET")
        handler = MainHandlerTestable(request=request, instance=Node.root())
        panels = handler.panels(path="", original="", mode="link")
        assert len(panels['panels']) == 2
        assert panels['path'] == root.get_absolute_url()

        root_panel = panels['panels'][1]
        assert root_panel['context']['selectable']
        assert root_panel['context']['instance']['addables']
        children = root_panel['context']['instance']['children']
        assert len(children) == 3
        assert set(x['path'] for x in children) == set((t.get_absolute_url(), i.get_absolute_url(), f.get_absolute_url()))
        for c in children:
            assert c['selectable']
            assert not c['selected']

    def test_root_children_image(self, client):
        """ panel in link image, ony image-ish content is selectable """
        root, t, i, f = self.setup_root_children()

        request = superuser_request("/", method="GET")
        handler = MainHandlerTestable(request=request, instance=Node.root())
        panels = handler.panels(path="", original="", mode="image")
        assert len(panels['panels']) == 2
        assert panels['path'] == Node.root().get_absolute_url()
        
        root_panel = panels['panels'][1]
        assert root_panel['context']['selectable']
        assert root_panel['context']['instance']['addables']
        children = root_panel['context']['instance']['children']
        assert len(children) == 3
        assert set(x['path'] for x in children) == set((t.get_absolute_url(), i.get_absolute_url(), f.get_absolute_url()))
        for c in children:
            if c['meta_type'] == 'testimage':
                assert c['selectable']
            else:
                assert not c['selectable']
            assert not c['selected']

    def test_subpanel_image(self, client):
        """
            handle subcontent, results in two panels
        """
        root, _, image1, _ = self.setup_root_children()

        request = superuser_request(image1.get_absolute_url(), method="GET")
        handler = MainHandlerTestable(request=request, instance=image1)
        
        panels = handler.panels(path=image1.get_absolute_url(), original="", mode="image")
        assert len(panels['panels']) == 3
        assert panels['path'] == image1.get_absolute_url()
        
        crumbs = panels['crumbs']['context']['crumbs']
        assert len(crumbs) == 2
        assert crumbs[0]['path'] == root.get_absolute_url()
        assert crumbs[1]['path'] == image1.get_absolute_url()

        root_panel = panels['panels'][1]
        children = root_panel['context']['instance']['children']
        assert len(children) == 3
        for c in children:
            if c['meta_type'] == 'testimage':
                assert c['selectable']
                assert c['selected']
            else:
                assert not c['selectable']
                assert not c['selected']

        image_panel = panels['panels'][2]
        assert not image_panel['context']['instance']['children']
        assert not image_panel['context']['instance']['addables']
