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
        Event.instances = []

        self.difficulty = 100
        self.create_events()

    @staticmethod
    async def reset_game():
        """Print the game's statistics, reset all game data, and start a new game."""
        pass  # This will be worked on later

    async def update_camp_status(self, reset_camp_data=False):
        """Updates the camp's status message in the #camp-status text channel."""
        async with self.client.db.acquire() as conn:
            if reset_camp_data is True:
                print('Reset camp data')
                query = '''INSERT INTO global VALUES ('fuel_use', 5) ON CONFLICT (name) DO UPDATE SET value = 5;
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
    
    async def spend_camp_fuel(self):
        """Removes a specified amount of fuel out of the camp's warehouse once a day."""
        async with self.client.db.acquire() as conn:
            pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
            fuel_use = (await self.client.utils.get_camp_resources(conn, 'fuel_use'))[0]['value']
            fuel = pop * fuel_use
            result = await self.client.utils.set_camp_resources(conn, {'fuel': -fuel})

            if result == 'The camp doesn\'t have enough fuel.':
                msg = (f'**The Generator**\n'
                       f'We didn\'t get gather enough fuel in time to power the generator for yet another day. '
                       f'The generator is going to freeze within minutes due to the extreme cold and we won\'t be '
                       f'able to start it up again ever again.\n\nThis is the end for our camp. Farewell.')
                await self.reset_game()
            else:
                msg = (f'**The Generator**\n'
                       f'We have survived for yet another day. We spent **{fuel}** fuel refilling the generator.')

            await self.client.send_message(self.client.channels['town-hall'], msg)

    @staticmethod
    async def random_camp_event():
        """Randomly chooses and runs a camp event."""
        event = random.choice(Event.instances)  # TODO: Take rarity into account
        await event.start_event()

    @staticmethod
    def create_events():
        """Creates all the camp events."""
        async def getting_colder(client, title):
            await client.utils.set_camp_resources(client.db, {'fuel_use': 1})

            msg = (f'**{title}**\n'
                   f'The average temperature has dropped yet again. We have adjusted the generator and will have to '
                   f'use 1 more fuel per resident.')

            return await client.send_message(client.channels['town-hall'], msg)

        Event(title='Getting Colder', 
              type='announcement',
              start=getting_colder)

        async def surprise_attack(client, title):
            attack = random.randint(self.difficulty / 2, self.difficulty)
            scrap = random.randint(attack / 2, attack * 1.5)
            result = await client.utils.set_camp_resources(client.db, {'defense': -attack, 'scrap': scrap}, negative_to_zero=True)

            msg = (f'**{title}**\n'
                   f'A group of bandits has launched a surprise attack against our camp!\n')
            
            if result == 'The camp doesn\'t have enough defense.':
                msg += (f'We weren\'t able to hold them back and they got over our walls. '
                        f'They raided our warehouse and stole as many of our resources as they could carry. '
                        f'They also robbed some of our residents out of all their resources.')
                await client.utils.set_camp_resources(client.db, {'food': randint(attack / 2, attack),
                                                                  'materials': randint(attack / 2, attack),
                                                                  'medicine': randint(attack / 4, attack / 2),
                                                                  'scrap': randint(attack / 2, attack)},
                                                      negative_to_zero=True)
            else:
                msg += (f'Luckily we were able to withstand their attack. We killed some of them and looted '
                        f'their bodies, earning {scrap} scrap. We lost {attack} defense due to their attack.')

            return await client.send_message(client.channels['town-hall'], msg)

        Event(title='Surprise Attack',
              type='announcement',
              start=surprise_attack)

        async def blizzard_warning(client, title):
            async with client.db.acquire() as conn:
                pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')

            msg = (f'**{title}**\n'
                   f'Our systems have detected that a blizzard is coming in the next 24 hours. We will have to temporarily '
                   f'overload the generator in order to survive, and that\'ll require somewhere between **{pop * 5}** and '
                   f'**{pop * 12}** fuel, depending on the strength of the storm.\n')
            return await client.send_message(client.channels['town-hall'], msg)

        async def blizzard_warning_end(client, title):
            async with client.db.acquire() as conn:
                pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
                fuel = pop * random.randint(5, 12)
                result = await client.utils.set_camp_resources(conn, {'fuel': -fuel})

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

        Event(title='Blizzard Warning', 
              type='quest',
              length=dt.timedelta(hours=24),
              start=blizzard_warning, 
              end=blizzard_warning_end)

        async def epidemic(client, title):
            msg = (f'**{title}**\n'
                   f'There is an epidemic in our camp. A highly fatal disease in spreading at rapid speeds '
                   f'and has already taken multiple lives. We must stop it before it is too late. If we do not '
                   f'gather 1 medicine for every resident of our camp within 18 hours, things will get much worse.')

            return await client.send_message(client.channels['town-hall'], msg)

        async def epidemic_end(client, title):
            async with client.db.acquire() as conn:
                pop = await conn.fetchval('''SELECT COUNT(user_id) FROM players WHERE status = 'normal';''')
                result = await client.utils.set_camp_resources(conn, {'medicine': -pop})

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
                result = await client.utils.set_camp_resources(conn, {'medicine': -medicine})

            if result == 'The camp doesn\'t have enough medicine.':
                msg = (f'**{title}**\n'
                       f'We weren\'t able to stop the epidemic in time. The disease is now spreading too quickly to '
                       f'be stopped. It is the end for our camp.')
                await Events.reset_game()

            else:
                msg = (f'**{title}**\n'
                       f'We suffered many losses and barely didn\'t make it, but the disease has been eradicated. '
                       f'We had to spend **{medicine}** medicine.')

            await client.send_message(client.channels['town-hall'], msg)

        Event(title='The Epidemic',
              type='quest',
              length=dt.timedelta(hours=18),
              start=epidemic,
              end=epidemic_end)


class Event:
    """
    There are three types of events:
        announcement - an event causes something to happen, no interactivity
        quest - some requirement must be met in a given amount of time
        vote - users decide what happens, may have requirements as well
    """
    instances = []
    client = None
    end_events_immediately = False

    def __init__(self, **kwargs):
        self.title = kwargs.pop('title')
        self.type = kwargs.pop('type')
        self.length = kwargs.get('length', dt.timedelta(hours=12))  # How long the event will run before it ends
        self.start = kwargs.pop('start')  # Function that is executed when the event starts
        self.end = kwargs.get('end')  # Optional function that is executed when the event ends

        if kwargs.get('add_to_instances', True):
            Event.instances.append(self)

    async def start_event(self, wait=True):
        """Starts an event and optionally schedules a date for it to end."""
        event_message = await self.start(self.client, self.title)

        if self.end_events_immediately:
            run_date = dt.datetime.now() + dt.timedelta(seconds=5)
        else:
            run_date = dt.datetime.now() + self.length

        if self.end is not None:
            print(run_date)
            self.client.scheduler.add_job(self.end_event,
                                          'date',
                                          run_date=run_date,
                                          args=[event_message.id],
                                          jobstore='persistent')

    @classmethod
    async def end_event(cls, event_id):
        """Ends an event by executing its end function."""
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
