import discord
from discord.ext import commands
import traceback

from config import *


class Core:
    """
    Extension loading/unloading and general-purpose commands.
    """

    def __init__(self, client):
        self.client = client

    async def on_ready(self):
        """Called when the bot is ready."""
        # Get the Server object
        self.client.server = self.client.get_server(SERVER_ID)

        # Create a list of this server's Channel objects
        for channel in self.client.server.channels:
            self.client.channels[channel.name] = self.client.get_channel(channel.id)

        # Start the scheduler
        self.client.scheduler.start()
        self.client.scheduler.print_jobs()

        # Change status message
        await self.client.change_presence(game=discord.Game(name='Survived for 0 days'))
        print(f'Ready!\nUser: {self.client.user.name} ({self.client.user.id})\n'
              f'Server: {self.client.server.name} ({self.client.server.id})')

    async def on_member_join(self, member):
        """Called when a new member joins the server."""
        msg = (f'Welcome to **The Camp**, {member.mention}!\n'
               f'Most of the commands related to the game are sent in private messages.\n'
               f'To join the camp, simply type `!join` here.')
        await self.client.send_message(member, msg)

    async def on_command_error(self, error, ctx):
        """Called on errors."""
        if isinstance(error, commands.CommandNotFound):
            await self.client.send_message(ctx.message.channel, 'Unknown command. Type `!help` for a list of commands.')
        else:
            traceback.print_exception(type(error), error, error.__traceback__)

    @commands.command(pass_context=True)
    async def help(self, ctx):
        """Sends a help message."""
        help_string = (
            '**General Commands**\n'
            '`!help` - Show this list of commands.\n'
            '`!join` - Join a new game.\n'
            '\n**Player Commands**\n'
            '`!daily` - Get your daily food rations from the camp.\n'
            '`!status` - View information about your character.\n'
            '`!home` - View your resources and home status.\n'
            '`!build` - View a list of possible house upgrades.\n'
            '`!craft` - View your item inventory and possible crafting recipes.\n'
            '\n**Action Commands**\n'
            '`!farm <amount>` - Work in the farm to earn food rations.\n'
            '`!mine <amount>` - Work in the mine to earn materials and fuel.\n'
            '`!guard <amount>` - Work as a guard to increase camp defenses and earn scrap.\n'
        )

        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' in user_roles:
            help_string += (
                '\n**Admin Commands**\n'
                '`!shutdown` - Shut down the bot.\n'
                '`!<reload/load/unload>` - Reload, load, or unload an extension.\n'
                '`!say <message>` - Make the bot write a message.\n'
                '`!setdata <name> <value> <user>` - Sets a resource for a player.\n'
                '`!updatecampstatus` - Manually update the camp status message.\n'
                '`!event <name>` - Start an event with a given name.\n'
                '`!debug <1/0> - Turns debug mode on or off.\n'
                '`!printjobs` - Print a list of scheduled jobs in the console.\n'
            )

        help_string += '\n*If you are confused about some game mechanic, read the docs channel.*'

        await self.client.say(help_string)

    @commands.command(pass_context=True)
    async def join(self, ctx):
        """Makes a player join the game (creates/sets needed table rows)."""
        async def add_player(alive, new_player, energy):
            """
            Add a player to the camp by wiping his resources and giving him necessary roles.
            """

            tr = conn.transaction()
            await tr.start()

            try:
                if new_player:
                    query = '''INSERT INTO players (user_id, status) VALUES ($1, 'normal')'''
                    await conn.execute(query, ctx.message.author.id)
                else:
                    query = '''UPDATE players SET energy = $1, food = default, fuel = default,
                        medicine = default, materials = default, scrap = default, house_upgrades = default,
                        till_normal = NULL, last_crime = NULL, status = 'normal', last_energy = default
                        WHERE user_id = $2'''

                    await conn.execute(query, energy, ctx.message.author.id)
            except Exception as e:
                await tr.rollback()
                await self.client.say('Something went wrong! Please type `!join` again.')
                print(e)
                return False
            else:
                await tr.commit()

            if alive:
                status_role = discord.utils.get(self.client.server.roles, name='Alive')
            else:
                status_role = discord.utils.get(self.client.server.roles, name='Dead')

            survivor_role = discord.utils.get(self.client.server.roles, name='Survivor')  # TODO: Make it xp-based
            member = self.client.server.get_member(ctx.message.author.id)
            await self.client.add_roles(member, status_role, survivor_role)

        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' in user_roles:
            await self.client.say('You have already joined the camp.')
        elif 'Dead' in user_roles:
            await self.client.say('You have already joined this game. Since you are dead, you have to wait for the '
                                  'next game to start.')
        else:
            max_energy = 12

            async with self.client.db.acquire() as conn:
                query = '''SELECT status FROM players WHERE user_id = $1;'''
                result = await conn.fetch(query, ctx.message.author.id)

                if len(result) > 0 and result[0]['status'] in ('normal', None):
                    await self.client.say(
                        'Welcome back to **The Camp**!\n'
                        'Remember to spend the XP gained from your previous game using `!upgrade`.\n'
                        'To see a list of available commands, type `!help`.')

                    if result[0]['status'] == 'normal':
                        energy = 0
                    else:
                        energy = max_energy
                    await add_player(True, False, energy)

                elif len(result) == 0:
                    await self.client.say(
                        'Welcome to **The Camp**!\n'
                        'Since it is your first time here, I\'d recommend reading the tutorial.\n'
                        'To see a list of available commands, type `!help`.')
                    await add_player(True, True, 12)

                elif len(result) > 0 and result[0]['status'] == 'dead':
                    await self.client.say('You have already died this game! Please wait for the next one to start.')
                    await add_player_roles(False, False, 0)

                else:
                    await self.client.say('Something went wrong!')


def setup(client):
    client.add_cog(Core(client))
