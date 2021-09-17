from discord import Embed
from asyncpg.pool import Pool, PoolConnectionProxy
import datetime


# Utility commands that are used by multiple cogs


async def get_user_roles(server, user):
    return [role.name for role in server.get_member(user.id).roles]


async def get_user_columns(db, user, *args):
    async def select_columns(conn):
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


async def set_resources(db, user, columns, resources, user_result=None, negative_to_zero=False):
    async def run_queries(conn):
        camp_query = await set_camp_resources(conn, resources, False, negative_to_zero)
        if type(camp_query) is str:  # Error
            return camp_query

        user_query = await set_user_resources(conn, user, columns, False, user_result)
        if type(user_query) is str:  # Error
            return user_query

        tr = conn.transaction()
        await tr.start()
        try:
            await conn.execute(camp_query['query'])
            await conn.execute(user_query['query'], *user_query['args'])
        except Exception as e:
            await tr.rollback()
            print(e)
            return 'Something went wrong!'
        else:
            await tr.commit()
            return True

    result = 'Something went wrong!'
    if type(db) == Pool:
        async with db.acquire() as c:
            result = await run_queries(c)
    elif type(db) == PoolConnectionProxy:
        result = await run_queries(db)
    return result


async def set_user_resources(db, user, columns, execute_query=True, user_result=None):
    async def update_columns(conn):
        last_energy = None
        column_list = list(columns.keys())

        if 'energy' in column_list:
            column_list.append('last_energy')
            if not isinstance(columns['energy'], tuple):
                if 'food' not in column_list:
                    column_list.append('food')
                columns['food'] = columns.get('food', 0) + columns['energy']  # Spend food equal to energy

        if user_result is None:
            query = f'''SELECT {','.join(column_list)} FROM players WHERE user_id = $1;'''
            result = dict(await conn.fetchrow(query, user.id))
        else:
            result = dict(user_result)

        # If the energy column is affected, then first update it
        if 'energy' in column_list:
            # TODO: Energy should also consume food
            max_energy = 12  # Make max energy upgradable later on in the game (and keep it in the db)

            last_energy, energy = await update_user_energy(result['last_energy'],
                                                           result['energy'],
                                                           max_energy)

            energy_gain = energy - result['energy']

            # print(f'*** energy before: {result["energy"]}')
            # print(f'*** energy after: {energy}')
            # print(f'*** energy gain: {energy_gain}')

            result['energy'] += energy_gain
            if not isinstance(columns['energy'], tuple):  # Do not increase in case of absolute value
                columns['energy'] += energy_gain

        # Generate the query
        sets = []
        for key, value in columns.items():
            if isinstance(value, tuple) and value[1] is False:  # Absolute
                if isinstance(value[0], str):
                    sets.append(f'{key} = \'{value[0]}\'')
                else:
                    sets.append(f'{key} = {value[0]}')
            else:  # Relative
                if result[key] < value * -1:  # Would result in a negative number
                    return f'You don\'t have enough {key}.'
                sets.append(f'{key} = {key} + {value}')

        if execute_query:
            tr = conn.transaction()
            await tr.start()
            try:
                if 'energy' in column_list:
                    query = f'''UPDATE players SET {','.join(sets)}, last_energy = $1 WHERE user_id = $2'''
                    await conn.execute(query, last_energy, user.id)
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
        else:  # Instead of executing, just return the query string and args
            if 'energy' in column_list:
                return {
                    'query': f'''UPDATE players SET {','.join(sets)}, last_energy = $1 WHERE user_id = $2''',
                    'args': [last_energy, user.id]
                }
            else:
                return {
                    'query': f'''UPDATE players SET {','.join(sets)} WHERE user_id = $1''',
                    'args': [user.id]
                }

    status = 'Something went wrong!'

    if type(db) == Pool:
        async with db.acquire() as c:
            status = await update_columns(c)
    elif type(db) == PoolConnectionProxy:
        status = await update_columns(db)

    return status


async def set_camp_resources(db, resources, execute_query=True, negative_to_zero=False):
    async def update_data(conn):
        camp_list = [f'name = \'{name}\'' for name in resources.keys()]

        query = f'''SELECT name, value FROM global WHERE {' OR '.join(camp_list)};'''
        results = await conn.fetch(query)

        q = ''''''
        for result in results:
            if resources[result['name']] * -1 > result['value']:  # Would run out of resources
                if not negative_to_zero:
                    return f'The camp doesn\'t have enough {result["name"]}.'
                q += f'''UPDATE global SET value = 0 WHERE name = '{result['name']}';'''
            q += f'''UPDATE global SET value = value + {resources[result['name']]} WHERE name = '{result['name']}';'''

        if execute_query:
            tr = conn.transaction()
            await tr.start()

            try:
                await conn.execute(q)
            except Exception as e:
                await tr.rollback()
                print(e)
                return 'Something went wrong!'
            else:
                await tr.commit()
                return results
        else:
            return {
                'query': q
            }

    status = 'Something went wrong!'

    if type(db) == Pool:
        async with db.acquire() as c:
            status = await update_data(c)
    elif type(db) == PoolConnectionProxy:
        status = await update_data(db)

    return status


async def update_user_energy(timestamp, energy, max_energy):
    if isinstance(energy, tuple):
        energy = energy[0]

    age = datetime.datetime.now() - timestamp  # How much time has passed since last energy retrieval
    hours = age.days * 24 + age.seconds // 3600  # Convert to hours
    new_energy = min(max_energy, energy + hours)  # Add the energy
    leftover_time = age - datetime.timedelta(hours=hours)  # Minutes/seconds left once hours subtracted
    new_timestamp = datetime.datetime.now() - leftover_time  # Set the new timestamp

    return new_timestamp, new_energy


async def update_camp_status(client, reset_camp_data=False):
    async with client.db.acquire() as conn:
        if reset_camp_data:
            query = '''INSERT INTO global VALUES ('temp', -30) ON CONFLICT (name) DO UPDATE SET value = -30;
            INSERT INTO global VALUES ('defense', 100) ON CONFLICT (name) DO UPDATE SET value = 1000;
            INSERT INTO global VALUES ('food', 500) ON CONFLICT (name) DO UPDATE SET value = 500;
            INSERT INTO global VALUES ('fuel', 1000) ON CONFLICT (name) DO UPDATE SET value = 1000;
            INSERT INTO global VALUES ('medicine', 10) ON CONFLICT (name) DO UPDATE SET value = 10;
            INSERT INTO global VALUES ('materials', 0) ON CONFLICT (name) DO UPDATE SET value = 0;
            INSERT INTO global VALUES ('scrap', 500) ON CONFLICT (name) DO UPDATE SET value = 500;'''
            await conn.execute(query)
        try:
            query = '''SELECT * FROM global'''
            result = dict(await conn.fetch(query))
        except Exception as e:
            print(e)
            return
            
    # TODO: Only update camp resources if a self.camp_resources_changed is True
    status_embed = Embed(color=0x128f39)
    status_embed.add_field(name='Temperature', value=f'{result["temp"]}°C', inline=False)
    status_embed.add_field(name='Defense Points', value=result["defense"], inline=False)

    warehouse_embed = Embed(color=0xe59b16)
    warehouse_embed.add_field(name='Food', value=result["food"], inline=False)
    warehouse_embed.add_field(name='Fuel', value=result["fuel"], inline=False)
    warehouse_embed.add_field(name='Medicine', value=result["medicine"], inline=False)
    warehouse_embed.add_field(name='Materials', value=result["materials"], inline=False)
    warehouse_embed.add_field(name='Scrap', value=result["scrap"], inline=False)

    i = 0
    async for message in client.logs_from(client.channels['camp-status']):
        if message.author == client.user:
            if i == 0:
                await client.edit_message(message, new_content='**Warehouse**', embed=warehouse_embed)
            elif i == 1:
                await client.edit_message(message, new_content='**Camp Status**', embed=status_embed)
            i += 1
