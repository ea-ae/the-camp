import asyncio
import discord
from discord.ext import commands

import prettytable

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
    msg = ("""Welcome to **The Camp**, {0}!
All commands related to the game are sent in private messages.
To join the camp, simply type `!join`.""").format(member.mention)
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
        embed.add_field(name='Rank', value=rank, inline=True)
        embed.add_field(name='XP', value='{0} ({1} total)'.format(xp, xp_total), inline=True)
        embed.add_field(name='Health', value=health, inline=True)
        embed.add_field(name='Energy', value='{0}/10'.format(energy), inline=True)
        await client.say(embed=embed)


@client.command(pass_context=True)
async def say(ctx, *, msg):
    if 'Moderator' in await get_user_roles(ctx.message.author):
        await client.say(msg)


@client.command()
async def help():
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
    food = 725
    fuel = 205
    medicine = 53
    materials = 2509
    scrap = 9487

    days = 0
    temperature = -33
    defense = 5411

    status_table = prettytable.PrettyTable(['Name', 'Value'])
    status_table.align = 'r'
    status_table.add_row(['Days survived', days])
    status_table.add_row(['Temperature', str(temperature) + '°C'])
    status_table.add_row(['Defense points', '{:,}'.format(defense)])

    warehouse_table = prettytable.PrettyTable(['Resource', 'Amount'])
    warehouse_table.align = 'r'
    warehouse_table.add_row(['Food', '{:,}'.format(food)])
    warehouse_table.add_row(['Fuel', '{:,}'.format(fuel)])
    warehouse_table.add_row(['Medicine', '{:,}'.format(medicine)])
    warehouse_table.add_row(['Materials', '{:,}'.format(materials)])
    warehouse_table.add_row(['Scrap', '{:,}'.format(scrap)])

    async for message in client.logs_from(channels['camp-status']):
        if message.author == client.user:
            status = '**Camp Status**```{0}```**Warehouse**```{1}```'.format(status_table, warehouse_table)
            await client.edit_message(message, status)
            break


async def get_user_roles(user):
    """
    Takes in an User object and returns his roles in the server.
    """
    return [role.name for role in server.get_member(user.id).roles]

# Run the bot
client.run(TOKEN)
