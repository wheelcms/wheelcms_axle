from django.contrib.auth.models import Group, User
from twotest.util import create_request
from two.ol.base import Forbidden
from wheelcms_axle.tests.models import Type1
from wheelcms_axle.models import Node
from wheelcms_axle.main import MainHandler

import pytest

"""
    superuser can do all

    Anonymous can view published content
    Anonymous cannot view unpublished content
    Logged in user (non-manager) can view published content
    Logged in user (non-manager) cannot view unpublished content
    User in group managers can view published content
    User in group managers can view unpublished content
      .. can edit, delete
    test toolbar presence?

    Set permission in handler (?)
"""
class BasePermissionTest(object):
    has_access = False

    def setup(self):
        self.managers, _ = Group.objects.get_or_create(name="managers")
        self.normal, _ = User.objects.get_or_create(username="normal")
        self.manager, _ = User.objects.get_or_create(username="manager")
        self.manager.groups.add(self.managers)

    def setup_handler(self, user=None, method="GET", with_instance=False,
                      state="private"):
        ins = None
        if with_instance:
            cont = Type1(node=Node.root(), state=state).save()
            ins =  cont.node
        request = create_request(method, "/")
        if self.provide_user():
            request.user = self.provide_user()
        handler = MainHandler(request=request, instance=ins)
        return handler

    def provide_user(self):
        return None

    def check(self, method, **kw):
        if self.has_access:
            assert method(**kw)
        else:
            pytest.raises(Forbidden, method, **kw)

    def test_hasaccess(self, client):
        """ test the hasaccess method for anonymous """
        handler = self.setup_handler()
        if self.has_access:
            assert handler.hasaccess()
        else:
            assert not handler.hasaccess()

    def test_create_get(self, client):
        handler = self.setup_handler()
        self.check(handler.create, type="type1")

    def test_create_post(self, client):
        handler = self.setup_handler(method="POST")
        self.check(handler.create, type="type1")

    def test_update_get(self, client):
        handler = self.setup_handler(with_instance=True)
        self.check(handler.update)

    def test_update_post(self, client):
        handler = self.setup_handler(method="POST", with_instance=True)
        self.check(handler.update)

    def test_unpublished_view(self, client):
        handler = self.setup_handler(with_instance=True)
        self.check(handler.view)

    def test_published_view(self, client):
        handler = self.setup_handler(with_instance=True, state="published")
        res = handler.view()
        assert res

class TestPermissionsAnonymous(BasePermissionTest):
    pass

class TestPermissionsNormal(BasePermissionTest):
    def provide_user(self):
        return self.normal

class TestPermissionsManager(BasePermissionTest):
    has_access = True

    def provide_user(self):
        return self.manager

