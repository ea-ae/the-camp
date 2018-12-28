async def get_user_roles(server, user):
    return [role.name for role in server.get_member(user.id).roles]
