import auth

anonymous = auth.Role("wheelcms.anonymous", "Anonymous", "An anonymous visitor")
member = auth.Role("wheelcms.member", "Member", "Authenticated site member")
owner = auth.Role("wheelcms.owner", "Owner")
editor = auth.Role("wheelcms.editor", "Editor", "An editor can create/edit content")
reviewer = auth.Role("wheelcms.reviewer", "Reviewer", "A reviewer can publish content")
admin = auth.Role("wheelcms.admin", "Administrator")

all_roles = (anonymous, member, owner, editor, reviewer, admin)
