import discord
from discord.ext import commands
import asyncio
import asyncpg

from config import *


description = 'The Camp is a game about surviving together in a post-apocalypse world as long as possible.'
command_prefix = '!'
extensions = ['core', 'admin', 'camp', 'ranks', 'player']


def run():
    print('Connecting to database...')

    credentials = {
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME,
        'host': DB_HOST
    }

    loop = asyncio.get_event_loop()
    db = loop.run_until_complete(asyncpg.create_pool(**credentials))

    print('Initializing bot...')

    client = CampBot(db=db, description=description, command_prefix=command_prefix)
    client.remove_command('help')
    load_extensions(client)

    try:
        print('Logging in...')
        loop.run_until_complete(client.login(TOKEN))
        print('Connecting...')
        loop.run_until_complete(client.connect())
    except KeyboardInterrupt:
        print('KeyboardInterrupt!')
    finally:
        print('Closing database...')
        loop.run_until_complete(db.close())
        print('Logging out...')
        loop.run_until_complete(client.logout())

        pending = asyncio.Task.all_tasks(loop=loop)
        gathered = asyncio.gather(*pending, loop=loop)
        try:
            gathered.cancel()
            loop.run_until_complete(gathered)
            # we want to retrieve any exceptions to make sure that they don't nag us about it being un-retrieved.
            gathered.exception()
        except:
            pass

        loop.close()
        print('Logged out!')


class CampBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(description=kwargs.pop('description'), command_prefix=kwargs.pop('command_prefix'))
        self.db = kwargs.pop('db')
        self.server = None
        self.channels = {}


def load_extensions(client):
    for extension in extensions:
        try:
            client.load_extension(f'cogs.{extension}')
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension "{extension}": {type(e).__name__}\n{e}')


# Run the bot
run()


"""
class CampBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=kwargs.pop('command_prefix'))
        self.db = kwargs.pop('db')
        self.server = None
        self.channels = {}

    async def on_ready(self):
        self.server = self.get_server(SERVER_ID)
        for channel in self.server.channels:
            self.channels[channel.name] = self.get_channel(channel.id)

        await self.change_presence(game=discord.Game(name='Survived for 0 days'))
        print('(5/5) Ready!')

    async def on_member_join(self, member):
        msg = (f'Welcome to **The Camp**, {member.mention}!'
               f'All commands related to the game are sent in private messages.'
               f'To join the camp, simply type `!join`.')
        await self.send_message(member, msg)

    async def on_command_error(self, error, ctx):
        if isinstance(error, commands.CommandNotFound):
            await self.send_message(ctx.message.channel, 'Unknown command. Type `!help` for a list of commands.')

    @commands.command(pass_context=True)
    async def status(self, ctx):
        user_roles = await get_user_roles(ctx.message.author)
        if any([role in user_roles for role in ('Alive', 'Dead')]):
            if 'Professional' in user_roles:
                rank = 'Professional'
                color = 0xf04c4c
            elif 'Veteran' in user_roles:
                rank = 'Veteran'
                color = 0xd1810d
            elif 'Survivor' in user_roles:
                rank = 'Survivor'
                color = 0xf0ca12
            else:
                rank = 'None'
                color = 0xffffff

            # Temporary fake values
            xp = 59
            xp_total = 107
            health = 'Normal'
            energy = 10

            embed = discord.Embed(title=ctx.message.author.display_name, color=color)
            embed.set_thumbnail(url=ctx.message.author.avatar_url)
            embed.add_field(name='Rank', value=rank)
            embed.add_field(name='XP', value=f'{xp} ({xp_total} total)')
            embed.add_field(name='Health', value=health)
            embed.add_field(name='Energy', value=f'{energy}/10')
            await self.say(embed=embed)

    @commands.command(pass_context=True, aliases=['house', 'inventory'])
    async def home(self, ctx):
        user_roles = await get_user_roles(ctx.message.author)
        if any([role in user_roles for role in ('Alive', 'Dead')]):
            if 'Professional' in user_roles:
                color = 0xf04c4c
            elif 'Veteran' in user_roles:
                color = 0xd1810d
            elif 'Survivor' in user_roles:
                color = 0xf0ca12
            else:
                color = 0xffffff

            # Temporary fake values
            food = 17
            fuel = 5
            medicine = 0
            materials = 36
            scrap = 107

            embed = discord.Embed(title='Your House',
                                  description='View possible house upgrades by typing `!build`.',
                                  color=color)
            embed.set_author(name=ctx.message.author.display_name)
            embed.add_field(name='Food', value=food)
            embed.add_field(name='Fuel', value=fuel)
            embed.add_field(name='Medicine', value=medicine)
            embed.add_field(name='Materials', value=materials)
            embed.add_field(name='Scrap', value=scrap)
            await self.say(embed=embed)

    @commands.command(pass_context=True)
    async def say(self, ctx, *, msg):
        if 'Moderator' in await get_user_roles(ctx.message.author):
            await self.say(msg)

    @commands.command()
    async def help(self):
        # await self.generate_status_message()  # TEMP
        await self.say('I don\'t need any help from you right now, but thanks for asking.')

    @commands.command(pass_context=True)
    async def join(self, ctx):
        if await user_has_role(ctx.message.author, 'Alive'):
            await self.say('You have already joined the camp.')
        elif await user_has_role(ctx.message.author, 'Dead'):
            await self.say('You have already joined this game. Since you are dead, you have to wait till someone '
                           'revives you or the next game starts.')
        else:
            await self.say('Welcome to **The Camp**! If it is your first time here, be sure to read the tutorial '
                           'channel first. To see a list of available commands, type `!help`.')

    async def generate_status_message(self):
        # Temporary fake data
        population = 100
        hours = 60
        temperature = -33
        defense = 5411

        food = 725
        fuel = 205
        medicine = 60
        materials = 2509
        scrap = 9487

        status_embed = discord.Embed(color=0x128f39)
        status_embed.add_field(name='Population', value=population, inline=False)
        status_embed.add_field(name='Time Survived',
                               value=f'{int(hours / 24)} days and {hours % 24} hours', inline=False)
        status_embed.add_field(name='Temperature', value=f'{temperature}°C', inline=False)
        status_embed.add_field(name='Defense Points', value=defense, inline=False)

        warehouse_embed = discord.Embed(color=0xe59b16)
        warehouse_embed.add_field(name='Food', value=food, inline=False)
        warehouse_embed.add_field(name='Fuel', value=fuel, inline=False)
        warehouse_embed.add_field(name='Medicine', value=medicine, inline=False)
        warehouse_embed.add_field(name='Materials', value=materials, inline=False)
        warehouse_embed.add_field(name='Scrap', value=scrap, inline=False)

        i = 0
        async for message in self.logs_from(channels['camp-status']):
            if message.author == self.user:
                if i == 0:
                    await self.edit_message(message, new_content='**Warehouse**', embed=warehouse_embed)
                elif i == 1:
                    await self.edit_message(message, new_content='**Camp Status**', embed=status_embed)
                i += 1

    async def get_user_roles(self, user):
        return [role.name for role in server.get_member(user.id).roles]
"""
