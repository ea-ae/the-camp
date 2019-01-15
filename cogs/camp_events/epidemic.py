from .. import events
import datetime as dt


async def epidemic(client, title):
    msg = (f'**{title}**\n'
           f'There is an epidemic in our camp. A highly fatal disease in spreading at rapid speeds '
           f'and has already taken multiple lives. We must stop it before it is too late. If we do not '
           f'gather 1 medicine for every resident of our camp within 18 hours, things will get much worse.')

    return await client.send_message(client.channels['town-hall'], msg)


async def epidemic_end(client, title):
    async with client.db.acquire() as conn:
        pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
        result = await client.utils.set_camp_data(conn, {'medicine': -pop})

    if result == 'The camp doesn\'t have enough medicine.':
        msg = (f'**{title}**\n'
               f'We do not have enough medical supplies to stop the epidemic! Things are even more serious '
               f'now. The disease is spreading even quicker and before, and if we do not stop it in the '
               f'next 6 hours, then it will be too late. We now need 2 medicine per resident to stop the '
               f'epidemic.')

        last_chance_event = Event(title='The Epidemic',
                                  type='announcement',
                                  length=dt.timedelta(hours=6),
                                  start=epidemic_last_chance,
                                  add_to_instances=False)
        await client.send_message(client.channels['town-hall'], msg)
        await last_chance_event.start_event()
    else:
        msg = (f'**{title}**\n'
               f'We stopped the epidemic in time and spent **{pop}** medicine.')
        await client.send_message(client.channels['town-hall'], msg)


async def epidemic_last_chance(client, title):
    async with client.db.acquire() as conn:
        pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
        medicine = pop * 2
        result = await client.utils.set_camp_data(conn, {'medicine': -medicine})

    if result == 'The camp doesn\'t have enough medicine.':
        msg = (f'**{title}**\n'
               f'We weren\'t able to stop the epidemic in time. The disease is now spreading too quickly to '
               f'be stopped. It is the end for our camp.')
        
        events = client.get_cog('Events')
        await events.reset_game()

    else:
        msg = (f'**{title}**\n'
               f'We suffered many losses and barely didn\'t make it, but the disease has been eradicated. '
               f'We had to spend **{medicine}** medicine.')

    await client.send_message(client.channels['town-hall'], msg)


def add_event():
    events.Event(title='The Epidemic',
                 type='quest',
                 length=dt.timedelta(hours=18),
                 start=epidemic,
                 end=epidemic_end)
