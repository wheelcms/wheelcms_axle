from wheelcms_axle.main import MainHandler
from wheelcms_axle.models import Node

from wheelcms_axle.tests.models import Type1
from twotest.util import create_request
from django.contrib.auth.models import User, Group

from two.ol.base import Redirect
import pytest

class TestOwnership(object):
    def setup(self):
        """ create a user """
        managers = Group.objects.get_or_create(name="managers")[0]
        self.user, _ = User.objects.get_or_create(username="jdoe")
        self.user.groups.add(managers)

    def test_save_model(self, client):
        """ saving a model should, by default, not set the owner
            (it can't) """
        type = Type1().save()
        assert type.owner is None

    def test_handler_create(self, client):
        """ The handler *can* set the user """
        request = create_request("POST", "/create",
                                 data=dict(title="Test",
                                           slug="test",
                                           language="en"))
        request.user = self.user

        root = Node.root()
        handler = MainHandler(request=request, post=True,
                              instance=dict(parent=root))
        pytest.raises(Redirect, handler.create, type=Type1.get_name())

        node = Node.get("/test")
        assert node.content().title == "Test"
        assert node.content().owner == self.user
