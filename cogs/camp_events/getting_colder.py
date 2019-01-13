from .. import events


async def getting_colder(client, title):
    await client.utils.set_camp_data(client.db, {'fuel_use': 1})

    msg = (f'**{title}**\n'
           f'The average temperature has dropped yet again. We have adjusted the generator and will have to '
           f'use 1 more fuel per resident.')

    return await client.send_message(client.channels['town-hall'], msg)


def add_event():
    events.Event(title='Getting Colder',
                 type='announcement',
                 start=getting_colder)
