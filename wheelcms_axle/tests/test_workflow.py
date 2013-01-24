"""
    Test the workflows
"""
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

    def test_is_published_false(self):
        """ verify a spoke isn't published """
        class DummyContent(object):
            state = "private"
        class DummyType(object):
            instance = DummyContent()
        assert not DefaultWorkflow(DummyType()).is_published()

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
        form = Type1Type.form()
        assert form.workflow_choices() == Type1Type.workflowclass.states
        assert form.workflow_default() == Type1Type.workflowclass.default

    def test_form_choices_instance(self, client):
        """ and it's value should be taken from the instance """
        data = Type1(state="published")
        data.save()
        form = Type1Type.form(instance=data)
        assert form['state'].value() == "published"
