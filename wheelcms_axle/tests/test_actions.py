import pytest
import mock

from drole.types import Permission

from ..node import Node
from .models import Type1, Type1Type
from .test_handler import MainHandlerTestable, superuser_request

from ..actions import ActionRegistry, action_registry, action


@pytest.mark.usefixtures("localtyperegistry")
class TestAction(object):
    type = Type1Type

    def setup(self):
        self.action_registry = ActionRegistry()
        action_registry.set(self.action_registry)

    def test_handler_action_decorator_root(self, client):
        root = Node.root()
        Type1(node=root, title="Root").save()
        #child = root.add("child")
        #Type1(node=child, title="Child").save()
        request = superuser_request("/+hello")
        handler = MainHandlerTestable(request=request, instance=root,
                                      kw=dict(action="hello"))
        result = handler.view()
        assert len(result) == 5
        result, request, handler, spoke, action = result
        assert result == "Hello"
        assert request
        assert handler
        assert action == "hello"
        assert spoke.instance == root.content()

    def test_handler_action_decorator_child(self, client):
        root = Node.root()
        Type1(node=root, title="Root").save()
        child = root.add("child")
        Type1(node=child, title="Child").save()
        request = superuser_request("/child/+hello")
        handler = MainHandlerTestable(request=request, instance=child,
                                      kw=dict(action="hello"))
        result = handler.view()
        assert len(result) == 5
        result, request, handler, spoke, action = result
        assert result == "Hello"
        assert request
        assert handler
        assert action == "hello"
        assert spoke.instance == child.content()

    def test_decorator_direct(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        h = self.action_registry.get('hello', spoke=spoke)
        assert h == spoke.hello

    def test_decorator_direct_override(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="hello", spoke=spoke)
        h = action_registry.get('hello', spoke=spoke)
        assert h == handler

    def test_match_spoke_path(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="hello",
                                      spoke=spoke, path="/foo")
        h = action_registry.get('hello', spoke=spoke, path="/foo")
        assert h == handler

    def test_match_spoke(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="hello",
                                      spoke=spoke)
        h = action_registry.get('hello', spoke=spoke)
        assert h == handler

    def test_match_path(self, client):
        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="hello",
                                      path="/foo")
        h = action_registry.get('hello', path="/foo")
        assert h == handler

    def test_match_global(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="hello")
        assert action_registry.get('hello') == handler
        assert action_registry.get('hello', path="/foo") == handler
        assert action_registry.get('hello', spoke=spoke) == handler
        assert action_registry.get('hello', spoke=spoke, path="/foo") == handler

    def test_simple_nomatch(self, client):
        h = action_registry.get('world')
        assert h is None

    def test_not_specific_enough(self, client):
        spoke = Type1(node=Node.root(), title="Root").save().spoke()

        def handler(*a, **b):
            pass

        self.action_registry.register(handler, action="world",
                                      spoke=spoke, path="/foo")
        assert action_registry.get('world', spoke=spoke) is None
        assert action_registry.get('world',  path="/foo") is None
        assert action_registry.get('world') is None


class TestActionDecorator(object):
    """ Test the @action decorater, user to mark a function/method as a valid
        action and (optionally) set a required permission """
    def test_no_perm(self):
        """ traditional "@action def foo()" with no permission specified """
        m = mock.MagicMock()
        action(m)
        assert m.action
        assert m.permission is None

    def test_permission(self):
        """ @action(perm) def foo() variant, should set permission """
        m = mock.MagicMock()
        action(Permission("foo"))(m)
        assert m.action
        assert m.permission == Permission("foo")
