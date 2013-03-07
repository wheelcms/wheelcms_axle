from stracks_api.api import Action, Entity, DjangoUser

# entities
user = DjangoUser() # Entity("user/user")
site = Entity("site/site")
page = Entity("page/page")
# object = Entity("object/object")
ipaddress = Entity("ipaddress/ipaddress")
useragent = Entity("user-agent/user-agent")
content = Entity("content/content")

# actions
create = Action("create")
view = Action("view")
edit = Action("edit")
delete = Action("delete")
login = Action("login")
logout = Action("logout")
crash = Action("crash")
