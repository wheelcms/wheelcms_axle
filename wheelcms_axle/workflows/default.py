class Workflow(object):
    def __init__(self, spoke):
        self.spoke = spoke

"""
    Define states as classes and the available transitions between them
    published = State("Published", dest=(Private,))
    private = State("Private", dest=(Visible, Published))

"""
class DefaultWorkflow(Workflow):
    PRIVATE = "private"
    VISIBLE = "visible"
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"

    states = ((PRIVATE, "Private"),
              (VISIBLE, "Visible"),
              (PENDING, "Pending"),
              (PUBLISHED, "Published"),
              (REJECTED, "Rejected"))

    default = PRIVATE

    def is_published(self):
        return self.spoke.instance.state == self.PUBLISHED

    def is_visible(self):
        return self.is_published() or self.spoke.instance.state == self.VISIBLE

    def state(self):
        return dict(self.states)[self.spoke.instance.state]
