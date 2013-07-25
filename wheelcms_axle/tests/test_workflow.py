"""
    Test the workflows
"""
from wheelcms_axle.models import Node

from wheelcms_axle.workflows.default import DefaultWorkflow
from wheelcms_axle.tests.models import Type1, Type1Type

class TestDefaultWorkflow(object):
    """
        Test the default workflow
    """
    def test_is_published_true(self):
        """ verify a spoke is published """
        class DummyContent(object):
            state = "published"
        class DummyType(object):
            instance = DummyContent()

        assert DefaultWorkflow(DummyType()).is_published()

    def test_is_published_false_private(self):
        """ verify a spoke isn't published """
        class DummyContent(object):
            state = "private"
        class DummyType(object):
            instance = DummyContent()
        assert not DefaultWorkflow(DummyType()).is_published()

    def test_is_published_false_visible(self):
        """ verify a visible spoke isn't published """
        class DummyContent(object):
            state = "visible"
        class DummyType(object):
            instance = DummyContent()
        assert not DefaultWorkflow(DummyType()).is_published()

    def test_is_visible_false_private(self):
        """ verify a private spoke isn't visible """
        class DummyContent(object):
            state = "private"
        class DummyType(object):
            instance = DummyContent()
        assert not DefaultWorkflow(DummyType()).is_visible()

    def test_is_visible_visible(self):
        """ verify a visible spoke is visible """
        class DummyContent(object):
            state = "visible"
        class DummyType(object):
            instance = DummyContent()
        assert DefaultWorkflow(DummyType()).is_visible()

    def test_is_visible_published(self):
        """ verify a published spoke is visible """
        class DummyContent(object):
            state = "published"
        class DummyType(object):
            instance = DummyContent()
        assert DefaultWorkflow(DummyType()).is_visible()

    def test_content_default(self, client):
        """ default should be set if not specified """
        data = Type1()
        data.save()
        assert data.state == data.spoke().workflow().default

    def test_content_default_update(self, client):
        """ but left untouched on update """
        data = Type1(state="published")
        data.save()
        assert data.state == "published"

    def test_form_choices(self):
        """ the form should get its choices from the workflow """
        form = Type1Type.form(parent=Node.root())
        assert form.workflow_choices() == Type1Type.workflowclass.states
        assert form.workflow_default() == Type1Type.workflowclass.default

    def test_form_choices_instance(self, client):
        """ and it's value should be taken from the instance """
        data = Type1(state="published")
        data.save()
        form = Type1Type.form(parent=Node.root(), instance=data)
        assert form['state'].value() == "published"

from wheelcms_axle.workflows.default import worklist

class TestWorklist(object):
    def test_empty(self, client):
        """ No content means no worklist """
        assert worklist().count() == 0

    def test_attached_pending(self, client):
        """ pending and attached, the way we like it """
        t = Type1(node=Node.root(), state="pending").save()
        assert worklist().count() == 1
        assert worklist()[0] == t.content_ptr

    def test_unattached_pending(self, client):
        """ unattached content cannot be accessed anyway """
        Type1(state="pending").save()
        assert worklist().count() == 0

    def test_attached_private(self, client):
        """ private content needs no explicit action """
        Type1(node=Node.root(), state="private").save()
        assert worklist().count() == 0

    def test_attached_published(self, client):
        """ published content needs no explicit action """
        Type1(node=Node.root(), state="published").save()
        assert worklist().count() == 0
