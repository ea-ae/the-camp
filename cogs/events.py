import discord
from discord.ext import commands
import datetime as dt
import random

from . import camp_events


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

        if self.type == 'vote':
            self.options = kwargs.pop('options')

        if kwargs.get('add_to_instances', True):
            Event.instances.append(self)

    async def start_event(self):
        """Starts an event and optionally schedules a date for it to end."""
        event_message = await self.start(self.client, self.title)

        if self.type == 'vote':
            # await self.client.say('1\u20e3 2\u20e3 3\u20e3 4\u20e3 5\u20e3 6\u20e3 7\u20e3 8\u20e3 9\u20e3')
            for i in range(1, min(10, self.options + 1)):
                await self.client.add_reaction(event_message, f'{i}\u20e3')

        # Schedule the event to end
        if self.end is not None:
            if self.end_events_immediately:
                run_date = dt.datetime.now() + dt.timedelta(seconds=5)
            else:
                run_date = dt.datetime.now() + self.length

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
                if instance.type == 'vote':
                    counts = [reaction.count for reaction in message.reactions]
                    # await cls.client.clear_reactions(message)

                    top = [i for i, j in enumerate(counts) if j == max(counts)]
                    choice = random.choice(top)

                    await instance.end(cls.client, instance.title, choice)
                else:
                    await instance.end(cls.client, instance.title)


class Events:
    """
    Events that are executed by the scheduler.
    """

    def __init__(self, client):
        self.client = client
        Event.client = client
        self.create_events()

    @commands.command(pass_context=True)
    async def reset_game(self, ctx='manual'):
        """Reset all game data and start a new game."""
        if type(ctx) is not str:
            user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
            if 'Developer' not in user_roles:
                return

        # Create game's table(s) if they don't exist yet
        q = '''
            CREATE TABLE IF NOT EXISTS players (
                user_id varchar(22) UNIQUE,
                status varchar(10),
                xp integer DEFAULT 0 NOT NULL,
                energy integer DEFAULT 12 NOT NULL,
                food integer DEFAULT 0 NOT NULL,
                fuel integer DEFAULT 0 NOT NULL,
                medicine integer DEFAULT 0 NOT NULL,
                materials integer DEFAULT 0 NOT NULL,
                scrap integer DEFAULT 0 NOT NULL,
                inventory text DEFAULT '{}'::text NOT NULL,
                house_upgrades text DEFAULT '{}'::text NOT NULL,
                character_upgrades text DEFAULT '{}'::text NOT NULL,
                last_energy timestamp without time zone DEFAULT now() NOT NULL,
                till_normal timestamp without time zone,
                last_crime timestamp without time zone,
                last_daily timestamp without time zone
            );
            CREATE TABLE IF NOT EXISTS global (
                name varchar(20) UNIQUE,
                value integer
            );
        '''
        async with self.client.db.acquire() as conn:
            await conn.execute(q)

        # Create and update camp data
        events = self.client.get_cog('Events')
        await events.update_camp_status(reset_camp_data=True)

        print('<--- GAME RESET DONE --->')

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
            fuel_use = (await self.client.utils.get_camp_data(conn, 'fuel_use'))[0]['value']
            fuel = pop * fuel_use
            result = await self.client.utils.set_camp_data(conn, {'fuel': -fuel})

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

        camp_events.blizzard_warning.add_event()
        camp_events.epidemic.add_event()
        camp_events.getting_colder.add_event()
        camp_events.paid_protection.add_event()
        camp_events.surprise_attack.add_event()


def setup(client):
    Event.instances = []
    client.add_cog(Events(client))
