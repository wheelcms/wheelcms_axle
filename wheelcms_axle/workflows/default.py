from django.dispatch import receiver
from ..signals import state_changed
from wheelcms_axle.content import Content

class Workflow(object):
    permission_assignment = {}
    default = "published"

    def __init__(self, spoke):
        self.spoke = spoke

"""
    Define states as classes and the available transitions between them
    published = State("Published", dest=(Private,))
    private = State("Private", dest=(Visible, Published))

"""

from wheelcms_axle import permissions as p, roles as r

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

    ## how to handle new/extra roles/permissions?
    ## Use below as initialization default, persist actual allocation
    ## in database?
    permission_assignment = {
            PRIVATE: {
                p.view_content:(r.owner, r.admin)
            },
            VISIBLE: {
                p.view_content:(r.anonymous, r.owner, r.admin, r.member)
            },
            PUBLISHED: {
                p.view_content:r.all_roles + (),
            },
            PENDING: {
                p.view_content:(r.owner, r.admin, r.member)
            },
            REJECTED: {
                p.view_content:(r.owner, r.admin, r.member)
            }
    }

    def is_published(self):
        return self.spoke.instance.state == self.PUBLISHED

    def is_visible(self):
        ## XXX deprecate this, should become a permission check
        return self.is_published() or self.spoke.instance.state == self.VISIBLE

    def state(self):
        return dict(self.states)[self.spoke.instance.state]

    def state_changed(self, oldstate, newstate):
        newperms = self.permission_assignment.get(newstate, ())
        if newperms:
            self.spoke.update_perms(newperms)


@receiver(state_changed, dispatch_uid="wheelcms_axle.workflow.state_changed")
def handle_state_changed(sender, oldstate, newstate, **kwargs):
    if isinstance(sender, Content):
        sender.spoke().workflow().state_changed(oldstate, newstate)


def worklist():
    """
        Return all attached content with a non-final state.
        Currently, this assumes the hardcoded 'pending' state,
        but eventually all registered workflows should be
        queried for their states
    """
    from wheelcms_axle.content import Content
    pending = Content.objects.filter(state="pending", node__isnull=False)
    return pending

