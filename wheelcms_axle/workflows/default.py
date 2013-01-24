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
    PUBLISHED = "published"

    states = ((PRIVATE, "Private"),
              (VISIBLE, "Visible"),
              (PUBLISHED, "Published"))

    default = PRIVATE

    def is_published(self):
        return self.spoke.instance.state == self.PUBLISHED
