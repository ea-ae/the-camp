from asyncpg.pool import Pool, PoolConnectionProxy
import datetime


# Utility commands that are used by multiple cogs


async def get_user_roles(server, user):
    return [role.name for role in server.get_member(user.id).roles]


async def get_user_columns(db, user, *args):
    async def select_columns(conn):
        # TODO: Automatically call update_user_energy() when needed?
        try:
            query = f'''SELECT {','.join(args)} FROM players WHERE user_id = $1;'''
            return await conn.fetchrow(query, user.id)
        except Exception as e:
            print(e)
            return False

    result = False
    if type(db) == Pool:
        async with db.acquire() as c:
            result = await select_columns(c)
    elif type(db) == PoolConnectionProxy:
        result = await select_columns(db)
    return result


async def set_resources(db, user, columns):
    async def update_columns(conn):
        column_list = list(columns.keys())
        if 'energy' in column_list:
            column_list.append('last_energy')

        query = f'''SELECT {','.join(column_list)} FROM players WHERE user_id = $1;'''
        result = dict(await conn.fetchrow(query, user.id))  # We have to edit this data, so make it a dict

        # If the energy column is affected, then first update it
        last_energy = None
        if 'energy' in column_list:
            # TODO: Energy should also consume food
            max_energy = 12  # Make max energy upgradable later on in the game (and keep it in the db)
            print(f'*** energy before: {result["energy"]}')
            last_energy, energy = await update_user_energy(result['last_energy'], result['energy'], max_energy)
            print(f'*** energy after: {energy}')
            energy_gain = energy - result['energy']
            print(f'*** energy gain: {energy_gain}')
            columns['energy'] += energy_gain
            print(last_energy)
        # Generate the query
        sets = []
        for key, value in columns.items():
            if isinstance(value, tuple) and value[1] is False:  # Absolute
                sets.append(f'{key} = {value[0]}')
            else:  # Relative
                if result[key] < value * -1:  # Would result in a negative number
                    return f'You don\'t have enough {key}.'
                sets.append(f'{key} = {key} + {value}')

        tr = conn.transaction()
        await tr.start()

        try:
            if 'energy' in column_list:
                query = f'''UPDATE players SET {','.join(sets)}, last_energy = $1 WHERE user_id = $2'''
                row = await conn.execute(query, last_energy, user.id)
                print('Energy row result')
                print(row)
            else:
                query = f'''UPDATE players SET {','.join(sets)} WHERE user_id = $1'''
                await conn.execute(query, user.id)
        except Exception as e:
            await tr.rollback()
            print(e)
            return 'Something went wrong!'
        else:
            await tr.commit()
            return result

    status = 'Something went wrong!'
    if type(db) == Pool:
        async with db.acquire() as c:
            status = await update_columns(c)
    elif type(db) == PoolConnectionProxy:
        status = await update_columns(db)
    return status


async def update_user_energy(timestamp, energy, max_energy):
    age = datetime.datetime.now() - timestamp
    hours = age.seconds // 3600
    leftover_time = age - datetime.timedelta(hours=hours)
    new_energy = min(max_energy, energy + hours)
    new_timestamp = datetime.datetime.now() - leftover_time
    return new_timestamp, new_energy
