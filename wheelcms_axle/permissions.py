import auth

create_content = auth.Permission("wheelcms.create_content", "Create content")
edit_content = auth.Permission("wheelcms.edit_content", "Edit content")
view_content = auth.Permission("wheelcms.view_content", "View content")
delete_content = auth.Permission("wheelcms.delete_content", "Delete content")

list_content = auth.Permission("wheelcms.list_content", "List content(s)")
change_auth_content = auth.Permission("wheelcms.change_auth_content", "Modify authorization settings")
