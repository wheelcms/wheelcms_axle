import auth

anonymous = auth.Role("wheelcms.anonymous", "Anonymous", "An anonymous visitor")
member = auth.Role("wheelcms.member", "Member", "Authenticated site member")
owner = auth.Role("wheelcms.owner", "Owner")
editor = auth.Role("wheelcms.editor", "Editor")
admin = auth.Role("wheelcms.admin", "Administrator")

