"""
    Stuff to test:

    - newly created type gets roles assigned (signal/no signal?)
    - update of permissions
    - role determination for users
    - local roles

"""
from mock import patch, PropertyMock, MagicMock
import pytest

from drole.models import RolePermission

from wheelcms_axle import permissions as p, roles

from .models import Type1Type
from ..auth import has_access, Permission, Role, assign_perms

def permpatch(return_value):
    """ patch the default roles returned by Type1Type.permission_assignment """
    return patch("wheelcms_axle.tests.models.Type1Type.permission_assignment",
                 new_callable=PropertyMock(return_value=return_value))

@pytest.fixture
def testpermission():
    return Permission('testpermission')

@pytest.fixture
def testrole():
    return Role('testrole')

@pytest.mark.usefixtures("localtyperegistry")
class TestAssignments(object):
    type = Type1Type

    def test_assignment_blank(self, client):
        with permpatch({}):
            t = Type1Type.create()
            t.save()

            assert not RolePermission.assignments(t.instance).exists()

    def test_assignment(self, client):
        with permpatch({p.view_content:(roles.owner,)}):
            t = Type1Type.create()
            t.save()

            assert RolePermission.assignments(t.instance).count() == 1

    def test_assign_perms_explicit(self, client):
        with permpatch({}):
            t = Type1Type.create()
            t.save()

            assign_perms(t.instance, {p.view_content: (roles.owner,)})

            assert RolePermission.assignments(t.instance).exists()
            a = RolePermission.assignments(t.instance).all()[0]

            assert a.role == roles.owner
            assert a.permission == p.view_content

    def test_assign_perms_twice(self, client):
        with permpatch({}):
            t = Type1Type.create()
            t.save()

            assign_perms(t.instance, {Permission("p1"): (Role("r1"),)})
            assign_perms(t.instance, {Permission("p2"): (Role("r2"),)})

            assert RolePermission.assignments(t.instance).count() == 2
            a = RolePermission.assignments(t.instance).all()

            assert set((x.role for x in a)) == set((Role("r1"), Role("r2")))
            assert set((x.permission for x in a)) == \
                   set((Permission("p1"), Permission("p2")))

    def test_assign_perms_duplicate(self, client):
        with permpatch({}):
            t = Type1Type.create()
            t.save()

            assign_perms(t.instance, {Permission("p"): (Role("r"),)})
            assign_perms(t.instance, {Permission("p"): (Role("r"),)})

            assert RolePermission.assignments(t.instance).count() == 1
            a = RolePermission.assignments(t.instance).all()[0]
            assert a.role == Role("r")
            assert a.permission == Permission("p")


class TestHasAccess(object):
    def test_has_access_class(self, testpermission, testrole):
        with permpatch({testpermission:(testrole,)}):
            with patch('wheelcms_axle.auth.get_roles_in_context',
                       return_value=set((testrole,))):
                request = MagicMock()
                assert has_access(request, Type1Type, None, testpermission)

    def test_no_access_class(self, testpermission, testrole):
        with permpatch({testpermission:(testrole,)}):
            with patch('wheelcms_axle.auth.get_roles_in_context',
                       return_value=set()):
                request = MagicMock()
                assert not has_access(request, Type1Type, None, testpermission)

    def test_has_access_instance(self, testpermission, testrole):
        with permpatch({testpermission:(testrole,)}):
            with patch('wheelcms_axle.auth.get_roles_in_context',
                       return_value=set((testrole,))):
                request = MagicMock()
                t = Type1Type.create().save()
                assert has_access(request, Type1Type, t, testpermission)

    def test_no_access_instance(self, testpermission, testrole):
        with permpatch({testpermission:(testrole,)}):
            with patch('wheelcms_axle.auth.get_roles_in_context',
                       return_value=set()):
                request = MagicMock()
                t = Type1Type.create().save()
                assert not has_access(request, Type1Type, t, testpermission)
