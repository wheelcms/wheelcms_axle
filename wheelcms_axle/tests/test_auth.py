"""
    Stuff to test:

    - newly created type gets roles assigned (signal/no signal?)
    - update of permissions
    - role determination for users
    - local roles

"""
import mock
import pytest

from drole.models import RolePermission

from .models import Type1Type, Type1

@pytest.mark.usefixtures("localtyperegistry")
class TestAuth(object):
    type = Type1Type

    def test_assignment_blank(self, client):
        with mock.patch("wheelcms_axle.tests.models.Type1Type.permission_assignment") as x:
            import pytest; pytest.set_trace()
            x.value = {}
            t = Type1Type.create()
            t.save()

            assert not RolePermission.assignments(t.instance).exists()
