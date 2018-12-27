import asyncio
import discord
from discord.ext import commands

from config import TOKEN, SERVER_ID


client = commands.Bot(command_prefix='!')
client.remove_command('help')

channels = {}
server = None


@client.event
async def on_ready():
    global server
    server = client.get_server(SERVER_ID)
    for channel in server.channels:
        channels[channel.name] = client.get_channel(channel.id)

    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)

    await client.change_presence(game=discord.Game(name='Survived for 0 days'))


@client.event
async def on_member_join(member):
    msg = (f'Welcome to **The Camp**, {member.mention}!'
           f'All commands related to the game are sent in private messages.'
           f'To join the camp, simply type `!join`.')
    await client.send_message(member, msg)


@client.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.CommandNotFound):
        await client.send_message(ctx.message.channel, 'Unknown command. Type `!help` for a list of commands.')


@client.command(pass_context=True)
async def status(ctx):
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
        await client.say(embed=embed)


@client.command(pass_context=True, aliases=['house', 'inventory'])
async def home(ctx):
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
        await client.say(embed=embed)


@client.command(pass_context=True)
async def say(ctx, *, msg):
    if 'Moderator' in await get_user_roles(ctx.message.author):
        await client.say(msg)


@client.command()
async def help():
    await generate_status_message()  # TEMP
    await client.say('I don\'t need any help from you right now, but thanks for asking.')


@client.command(pass_context=True)
async def join(ctx):
    if await user_has_role(ctx.message.author, 'Alive'):
        await client.say('You have already joined the camp.')
    elif await user_has_role(ctx.message.author, 'Dead'):
        await client.say('You have already joined this game. Since you are dead, you have to wait till someone revives '
                         'you or the next game starts.')
    else:
        await client.say('Welcome to **The Camp**! If it is your first time here, be sure to read the tutorial channel '
                         'first. To see a list of available commands, type `!help`.')


async def generate_status_message():
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
    async for message in client.logs_from(channels['camp-status']):
        if message.author == client.user:
            if i == 0:
                await client.edit_message(message, new_content='**Warehouse**', embed=warehouse_embed)
            elif i == 1:
                await client.edit_message(message, new_content='**Camp Status**', embed=status_embed)
            i += 1


async def get_user_roles(user):
    """
    Takes in an User object and returns his roles in the server.
    """
    return [role.name for role in server.get_member(user.id).roles]

# Run the bot
client.run(TOKEN)
