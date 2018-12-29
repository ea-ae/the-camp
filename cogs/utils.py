import datetime


# Utility commands that are used by multiple cogs


async def get_user_roles(server, user):
    return [role.name for role in server.get_member(user.id).roles]


async def set_user_resources():
    pass


async def update_user_energy(timestamp, energy, max_energy):
    age = datetime.datetime.now() - timestamp
    hours = age.seconds // 3600
    leftover_time = age - datetime.timedelta(hours=hours)
    new_energy = min(max_energy, energy + hours)
    new_timestamp = datetime.datetime.now() - leftover_time

    return new_timestamp, new_energy
