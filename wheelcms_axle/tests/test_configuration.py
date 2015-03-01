import pytest
import mock

from twotest.util import create_request
from ..base import Forbidden

from ..configuration import ConfigurationHandler
import wheelcms_axle.permissions as p

from .test_handler import superuser_request

class TestConfigurationHandler(object):
    """
        The configuration handler is responsible for handling
        multiple, dynamically addable, configuration tabs, classes
        and actions
    """
    def test_permission_view_denied(self, client):
        """ Verify view is guarded by modify_settings permission """
        with mock.patch("wheelcms_axle.auth.has_access") as m:
            m.return_value = False

            request = create_request("GET", "/@/configuration", data={})
            h = ConfigurationHandler()
            h.init_from_request(request)
            with pytest.raises(Forbidden):
                h.get(request)

            assert m.call_args[0][3] == p.modify_settings

    def test_permission_view_access(self, client):
        """ if permission is present, call should succeed """
        with mock.patch("wheelcms_axle.auth.has_access") as m:
            m.return_value = True

            request = create_request("GET", "/@/configuration", data={})
            h = ConfigurationHandler()
            h.init_from_request(request)
            assert h.get(request) is not None

            assert m.call_args[0][3] == p.modify_settings

    def test_permission_process_denied(self, client):
        """ Verify process is guarded by modify_settings permission """
        with mock.patch("wheelcms_axle.auth.has_access") as m:
            m.return_value = False
            request = create_request("POST", "/@/configuration", data={})
            h = ConfigurationHandler()
            h.init_from_request(request)
            with pytest.raises(Forbidden):
                h.post(request)

            assert m.call_args[0][3] == p.modify_settings

    def test_permission_process_access(self):
        """ if permission is present, call should succeed """
        with mock.patch("wheelcms_axle.auth.has_access") as m:
            m.return_value = True
            request = create_request("POST", "/@/configuration", data={})
            h = ConfigurationHandler()
            h.init_from_request(request)

            assert h.post(request) is not None

            assert m.call_args[0][3] == p.modify_settings

    def test_action_view(self, client):
        """ Verify an action gets forwarded appropriately """
        m = mock.Mock(**{"test.action":True})
        mklass = mock.Mock(return_value=m)

        request = superuser_request("/@/configuration", "GET", action="test")
        with mock.patch("wheelcms_axle.registries."
                        "configuration.configuration_registry.get",
                        return_value=mklass):
            h = ConfigurationHandler()
            h.init_from_request(request)
            h.get(request)

            assert m.test.call_args is not None

    def test_nonaction_view(self, client):
        """ Verify an action gets blocked appropriately """
        m = mock.Mock(**{"test.action":False})
        mklass = mock.Mock(return_value=m)

        request = superuser_request("/@/configuration", "GET", action="test")
        with mock.patch("wheelcms_axle.registries."
                        "configuration.configuration_registry.get",
                        return_value=mklass):
            h = ConfigurationHandler()
            h.init_from_request(request)
            h.get(request)

            assert m.test.call_args is None

    def test_action_process(self, client):
        """ Verify an action gets forwarded appropriately """
        m = mock.Mock(**{"test.action":True})
        mklass = mock.Mock(return_value=m)

        request = superuser_request("/@/configuration", "POST", action="test")
        with mock.patch("wheelcms_axle.registries."
                        "configuration.configuration_registry.get",
                        return_value=mklass):
            h = ConfigurationHandler()
            h.init_from_request(request)
            h.post(request)

            assert m.test.call_args is not None

    def test_nonaction_process(self, client):
        """ Verify an action gets forwarded appropriately """
        m = mock.Mock(**{"test.action":False})
        mklass = mock.Mock(return_value=m)

        request = superuser_request("/@/configuration", "POST", action="test")
        with mock.patch("wheelcms_axle.registries."
                        "configuration.configuration_registry.get",
                        return_value=mklass):
            h = ConfigurationHandler()
            h.init_from_request(request)
            h.process(request)

            assert m.test.call_args is None
