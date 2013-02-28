"""
    test permissions in the main handler
"""

from django.contrib.auth.models import Group, User
from twotest.util import create_request
from two.ol.base import Forbidden
from wheelcms_axle.tests.models import Type1
from wheelcms_axle.models import Node
from wheelcms_axle.main import MainHandler

import pytest


class BasePermissionTest(object):
    """
        Base test to be used against different types of users that may
        or may not have access """

    has_access = False

    def setup(self):
        """ create the managers group """
        self.managers, _ = Group.objects.get_or_create(name="managers")

    def setup_handler(self, user=None, method="GET", with_instance=False,
                      state="private"):
        """ setup the mainhandler """
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
        """ provide the user to test against. None = anonymous """
        return None

    def check(self, method, **kw):
        """ assert the test based on hasaccess """
        if self.has_access:
            assert method(**kw)
        else:
            pytest.raises(Forbidden, method, **kw)

    def test_hasaccess(self, client):
        """ only powerusers have access """
        handler = self.setup_handler()
        if self.has_access:
            assert handler.hasaccess()
        else:
            assert not handler.hasaccess()

    def test_create_get(self, client):
        """ only powerusers can get the createform """
        handler = self.setup_handler()
        self.check(handler.create, type=Type1.get_name())

    def test_create_post(self, client):
        """ only powerusers can post the createform """
        handler = self.setup_handler(method="POST")
        self.check(handler.create, type=Type1.get_name())

    def test_update_get(self, client):
        """ only powerusers can view the update form """
        handler = self.setup_handler(with_instance=True)
        self.check(handler.update)

    def test_update_post(self, client):
        """ only powerusers can post updates """
        handler = self.setup_handler(method="POST", with_instance=True)
        self.check(handler.update)

    def test_unpublished_view(self, client):
        """ unpublished content is only visible to power users """
        handler = self.setup_handler(with_instance=True)
        self.check(handler.view)

    def test_published_view(self, client):
        """ published content is always visible """
        handler = self.setup_handler(with_instance=True, state="published")
        res = handler.view()
        assert res

    def test_published_expired_view(self, client):
        """ expired content should not be accessible """
        pytest.skip("To be implemented XXX")

    def test_toolbar(self, client):
        """ test if toolbar is/should be visible or not """
        pytest.skip("To be implemented XXX")

class TestPermissionsAnonymous(BasePermissionTest):
    """ anonymous has no access """
    pass


class TestPermissionsNormal(BasePermissionTest):
    """ an ordinary user has no access """
    def provide_user(self):
        """ create an ordinary user """
        normal, _ = User.objects.get_or_create(username="normal")
        return normal


class TestPermissionsManager(BasePermissionTest):
    """ a manager has access """
    has_access = True

    def provide_user(self):
        """ create a manager """
        manager, _ = User.objects.get_or_create(username="manager")
        manager.groups.add(self.managers)
        return manager


class TestPermissionsSuperuser(BasePermissionTest):
    """ A superuser has access, even if he's not a manager """
    has_access = True

    def provide_user(self):
        """ create a non-manager superuser """
        superuser, _ = User.objects.get_or_create(username="superuser",
                                                  is_superuser=True)
        return superuser


class TestPermissionsInactiveSuperuser(BasePermissionTest):
    """ an inactive superuser has no access """
    has_access = False

    def provide_user(self):
        """ create an inactive superuser """
        superuser, _ = User.objects.get_or_create(username="superuser",
                                                  is_superuser=True,
                                                  is_active=False)
        return superuser


class TestPermissionsInactiveManager(BasePermissionTest):
    """ an inactive manager has no access """
    has_access = False

    def provide_user(self):
        """ create an inactive manager """
        manager, _ = User.objects.get_or_create(username="manager",
                                                is_active=False)
        manager.groups.add(self.managers)
        return manager
