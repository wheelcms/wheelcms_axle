"""
    test permissions in the main handler
"""

from django.contrib.auth.models import Group, User, AnonymousUser
from twotest.util import create_request
from wheelcms_axle.base import Forbidden
from wheelcms_axle.tests.models import Type1, Type1Type
from wheelcms_axle.models import Node
from wheelcms_axle.main import MainHandler
from wheelcms_axle import access

import pytest

@pytest.mark.usefixtures("localtyperegistry", "defaultworkflow")
class BasePermissionTest(object):
    """
        Base test to be used against different types of users that may
        or may not have access """
    type = Type1Type

    has_access = False

    def setup_handler(self, user=None, method="GET", with_instance=False,
                      state="private"):
        """ setup the mainhandler """
        root = Node.root()
        if with_instance:
            cont = Type1Type.create(node=root, state=state).save()
            cont.assign_perms()
        request = create_request(method, "/", data={'type':Type1.get_name()})
        if self.provide_user():
            request.user = self.provide_user()
        handler = MainHandler()
        handler.init_from_request(request)
        handler.instance = root

        return handler

    def provide_user(self):
        """ provide the user to test against """
        return AnonymousUser()

    def check(self, method, **kw):
        """ assert the test based on hasaccess """
        if self.has_access:
            assert method(**kw)
        else:
            pytest.raises(Forbidden, method, **kw)

    def test_hasaccess(self, client):
        """ only powerusers have access """
        if self.has_access:
            assert access.has_access(self.provide_user())
        else:
            assert not access.has_access(self.provide_user())

    def test_create_get(self, client):
        """ only powerusers can get the createform """
        handler = self.setup_handler()
        self.check(handler.create)

    def test_create_post(self, client):
        """ only powerusers can post the createform """
        handler = self.setup_handler(method="POST")
        self.check(handler.create)

    def test_update_get(self, client):
        """ only powerusers can view the update form """
        handler = self.setup_handler(with_instance=True)
        self.check(handler.edit)

    def test_update_post(self, client):
        """ only powerusers can post updates """
        handler = self.setup_handler(method="POST", with_instance=True)
        self.check(handler.edit)

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

    def test_published_view(self, client):
        handler = self.setup_handler(with_instance=True, state="published")
        self.check(handler.view)
