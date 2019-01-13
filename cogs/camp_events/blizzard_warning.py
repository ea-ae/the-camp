from .. import events
import random
import datetime as dt


async def blizzard_warning(client, title):
    async with client.db.acquire() as conn:
        pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')

    msg = (f'**{title}**\n'
           f'Our systems have detected that a blizzard is coming in the next 24 hours. We will have to '
           f'temporarily overload the generator in order to survive, and that\'ll require somewhere between '
           f'**{pop * 5}** and **{pop * 12}** fuel, depending on the strength of the storm.')
    return await client.send_message(client.channels['town-hall'], msg)


async def blizzard_warning_end(client, title):
    async with client.db.acquire() as conn:
        pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
        fuel = pop * random.randint(5, 12)
        result = await client.utils.set_camp_data(conn, {'fuel': -fuel})

        if result == 'The camp doesn\'t have enough fuel.':
            msg = (f'**{title}**\n'
                   f'It is too late. We weren\'t able to get enough fuel in time. This is the end for '
                   f'all of us. Farewell.')
            await Events.reset_game()
        else:
            msg = (f'**{title}**\n'
                   f'We have successfully overloaded the generator for **{fuel}** fuel and will hopefully '
                   f'survive the blizzard.')

    return await client.send_message(client.channels['town-hall'], msg)


def add_event():
    events.Event(title='Blizzard Warning',
                 type='quest',
                 length=dt.timedelta(hours=24),
                 start=blizzard_warning,
                 end=blizzard_warning_end)
