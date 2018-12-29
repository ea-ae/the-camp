from asyncpg.pool import Pool, PoolConnectionProxy
import datetime


# Utility commands that are used by multiple cogs


async def get_user_roles(server, user):
    return [role.name for role in server.get_member(user.id).roles]


async def get_user_columns(db, user, *args):
    async def select_columns(c):
        try:
            query = f'''SELECT {','.join(args)} FROM players WHERE user_id = $1;'''
            return await c.fetchrow(query, user.id)
        except Exception as e:
            print(e)
            return False

    result = False
    if type(db) == Pool:
        async with db.acquire() as conn:
            result = await select_columns(conn)
    elif type(db) == PoolConnectionProxy:
        result = await select_columns(db)
    return result


async def set_user_resources(conn, user, resources):
    resource_list = list(resources.keys())

    tr = conn.transaction()
    await tr.start()

    try:
        query = f'''SELECT {','.join(resource_list)} FROM players WHERE user_id = $1);'''
        result = await conn.fetchval(query, user.id)

        for key, value in resources.items():
            if isinstance(value, tuple):
                resource = value
                relative = value[1]
            else:
                resource = value
                relative = True

        query = '''INSERT INTO players (user_id, status) VALUES ($1, 'normal')'''
        await conn.execute(query, ctx.message.author.id)
    except Exception as e:
        await tr.rollback()

        print(e)
        return 'Something went wrong!'
    else:
        await tr.commit()
        return True


async def update_user_energy(timestamp, energy, max_energy):
    age = datetime.datetime.now() - timestamp
    hours = age.seconds // 3600
    leftover_time = age - datetime.timedelta(hours=hours)
    new_energy = min(max_energy, energy + hours)
    new_timestamp = datetime.datetime.now() - leftover_time

    return new_timestamp, new_energy
