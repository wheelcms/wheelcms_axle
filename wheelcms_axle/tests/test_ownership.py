import pytest

from wheelcms_axle.main import MainHandler
from wheelcms_axle.models import Node

from wheelcms_axle.tests.models import Type1, Type1Type
from twotest.util import create_request

from .fixtures import superuser


@pytest.mark.usefixtures("localtyperegistry")
class TestOwnership(object):
    type = Type1Type

    def test_save_model(self, client):
        """ saving a model should, by default, not set the owner
            (it can't) """
        type = Type1().save()
        assert type.owner is None

    def test_handler_create(self, superuser, client):
        """ The handler *can* set the user """
        request = create_request("POST", "/create",
                                 data=dict(title="Test",
                                           slug="test",
                                           language="en",
                                           type=Type1.get_name()))
        request.user = superuser

        handler = MainHandler()
        res = handler.dispatch(request, nodepath="", handlerpath="create")
        assert res.status_code == 302

        node = Node.get("/test")
        assert node.content().title == "Test"
        assert node.content().owner == superuser
