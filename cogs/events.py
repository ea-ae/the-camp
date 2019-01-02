import discord
from discord.ext import commands

import datetime as dt
import random


class Events:
    """
    Events that are executed by the scheduler.
    """

    def __init__(self, client):
        self.client = client
        Event.client = client
        self.create_events()

    async def update_camp_status(self, reset_camp_data=False):
        async with self.client.db.acquire() as conn:
            if reset_camp_data is True:
                print('Reset camp data')
                query = '''INSERT INTO global VALUES ('fuel_use', 10) ON CONFLICT (name) DO UPDATE SET value = 10;
                INSERT INTO global VALUES ('defense', 100) ON CONFLICT (name) DO UPDATE SET value = 1000;
                INSERT INTO global VALUES ('food', 500) ON CONFLICT (name) DO UPDATE SET value = 500;
                INSERT INTO global VALUES ('fuel', 1000) ON CONFLICT (name) DO UPDATE SET value = 1000;
                INSERT INTO global VALUES ('medicine', 10) ON CONFLICT (name) DO UPDATE SET value = 10;
                INSERT INTO global VALUES ('materials', 0) ON CONFLICT (name) DO UPDATE SET value = 0;
                INSERT INTO global VALUES ('scrap', 500) ON CONFLICT (name) DO UPDATE SET value = 500;'''
                await conn.execute(query)
            try:
                query = '''SELECT * FROM global;'''
                result = dict(await conn.fetch(query))
                query = '''SELECT COUNT(user_id) FROM players WHERE status = 'normal';'''
                population = await conn.fetchval(query)
            except Exception as e:
                print(e)
                return

        now = dt.datetime.now()
        tomorrow = now + dt.timedelta(days=1)
        t = dt.datetime.combine(tomorrow, dt.time.min) - now
        days, hours, minutes = t.days, t.seconds // 3600, t.seconds // 60 % 60

        # TODO: Only update camp resources if a self.camp_resources_changed is True
        status_embed = discord.Embed(color=0x128f39)
        status_embed.add_field(name='Population', value=population, inline=False)
        status_embed.add_field(name='Daily Generator Fuel Usage',
                               value=(f'{result["fuel_use"]} per person ({population * result["fuel_use"]} total)\n'
                                      f'Next fuel refill in {hours} hour{"s" if hours != 1 else ""} and '
                                      f'{minutes} minute{"s" if minutes != 1 else ""}'),
                               inline=False)
        status_embed.add_field(name='Defense Points', value=result["defense"], inline=False)

        warehouse_embed = discord.Embed(color=0xe59b16)
        warehouse_embed.add_field(name='Food', value=result["food"], inline=False)
        warehouse_embed.add_field(name='Fuel', value=result["fuel"], inline=False)
        warehouse_embed.add_field(name='Medicine', value=result["medicine"], inline=False)
        warehouse_embed.add_field(name='Materials', value=result["materials"], inline=False)
        warehouse_embed.add_field(name='Scrap', value=result["scrap"], inline=False)

        i = 0
        async for message in self.client.logs_from(self.client.channels['camp-status']):
            if message.author == self.client.user:
                if i == 0:
                    await self.client.edit_message(message, new_content='**Warehouse**', embed=warehouse_embed)
                elif i == 1:
                    await self.client.edit_message(message, new_content='**Camp Status**', embed=status_embed)
                i += 1

    @staticmethod
    async def random_camp_event():
        event = random.choice(Event.instances)  # TODO: Take rarity into account
        await event.start_event()

    @staticmethod
    def create_events():
        async def getting_colder(client, title):
            await client.utils.set_camp_resources(client.db, {'fuel_use': 1})

            msg = (f'**{title}**\n'
                   f'The average temperature has dropped yet again. We have adjusted the generator and will have to '
                   f'use 1 more fuel per person.')

            return await client.send_message(client.channels['town-hall'], msg)

        Event(title='Getting Colder', type='announcement', rarity=1, start=getting_colder)

        async def blizzard_warning(client, title):
            async with client.db.acquire() as conn:
                pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')

            msg = (f'**{title}**\n'
                   f'Our systems have detected that a blizzard is coming in 6 hours. We will have to temporarily '
                   f'overload the generator in order to survive, and that\'ll require somewhere between {pop * 5} and '
                   f'{pop * 12} fuel, depending on the strength of the storm.\n')
            return await client.send_message(client.channels['town-hall'], msg)

        async def blizzard_warning_end(client, title):
            async with client.db.acquire() as conn:
                pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
                fuel = pop * random.randint(5, 12)
                result = await client.utils.set_camp_resources(conn, {'fuel': -fuel})

                if type(result) == str and result == 'The camp doesn\'t have enough fuel.':
                    msg = (f'**{title}**\n'
                           f'It is too late. The weren\'t able to get enough fuel in time. '
                           f'We will all be dead within 30 minutes.')
                    # TODO: Schedule a function that will reset the game in 30 mins
                else:
                    msg = (f'**{title}**\n'
                           f'We have successfully overloaded the generator for {fuel} fuel and will hopefully '
                           f'survive the blizzard.')

            return await client.send_message(client.channels['town-hall'], msg)

        Event(title='Blizzard Warning', type='quest', start=blizzard_warning, end=blizzard_warning_end)


class Event:
    """
    There are three types of events:
        announcement - an event causes something to happen, no interactivity
        quest - some requirement must be met in a given amount of time
        vote - users decide what happens, may have requirements as well
    """
    instances = []
    client = None

    def __init__(self, **kwargs):
        self.title = kwargs.pop('title')
        self.type = kwargs.pop('type')
        self.length = kwargs.get('length', dt.timedelta(hours=12))  # How long the event will run before it ends
        self.start = kwargs.pop('start')  # Function that is executed when the event starts
        self.end = kwargs.get('end')  # Optional function that is executed when the event ends

        Event.instances.append(self)

    async def start_event(self):
        event_id = (await self.start(self.client, self.title)).id

        if self.end is not None:
            self.client.scheduler.add_job(self.end_event,
                                          'date',
                                          run_date=dt.datetime.now() + dt.timedelta(minutes=1),  # TEMPORARY!
                                          # run_date=dt.datetime.now() + event.length,
                                          args=[event_id],
                                          jobstore='persistent')

    @classmethod
    async def end_event(cls, event_id):
        try:
            message = await cls.client.get_message(cls.client.channels['town-hall'], event_id)
        except discord.errors.NotFound:
            print('Can\'t stop event as message was not found!')
            return False

        title = message.content.split('**')[1]

        for instance in cls.instances:  # Search for an event title with given title
            if instance.title == title:
                await instance.end(cls.client, instance.title)


def setup(client):
    client.add_cog(Events(client))
