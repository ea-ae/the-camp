import discord
from discord.ext import commands

from config import *
from .utils import get_user_roles


class Core:
    """
    Extension loading/unloading and general-purpose commands.
    """

    def __init__(self, client):
        self.client = client

    async def on_ready(self):
        self.client.server = self.client.get_server(SERVER_ID)
        for channel in self.client.server.channels:
            self.client.channels[channel.name] = self.client.get_channel(channel.id)

        # events_cog = self.client.get_cog('Events')
        # await events_cog.configure_scheduler()

        await self.client.change_presence(game=discord.Game(name='Survived for 0 days'))
        print(f'Ready!\nUser: {self.client.user.name} ({self.client.user.id})\n'
              f'Server: {self.client.server.name} ({self.client.server.id})')

    async def on_member_join(self, member):
        msg = (f'Welcome to **The Camp**, {member.mention}!\n'
               f'Most of the commands related to the game are sent in private messages.\n'
               f'To join the camp, simply type `!join` here.')
        await self.client.send_message(member, msg)

    async def on_command_error(self, error, ctx):
        if isinstance(error, commands.CommandNotFound):
            await self.client.send_message(ctx.message.channel, 'Unknown command. Type `!help` for a list of commands.')

    @commands.command()
    async def help(self):
        # await self.client.say('I don\'t need any help from you right now, but thanks for asking.')

        await self.client.say(
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
            '\n*If you are confused about some game mechanic, read the docs channel.*')

    @commands.command(pass_context=True)
    async def join(self, ctx):
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

        user_roles = await get_user_roles(self.client.server, ctx.message.author)
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
