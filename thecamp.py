import asyncio
import discord
from discord.ext import commands

import prettytable

from config import TOKEN


# Settings
SERVER_ID = '527261834852696064'

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
        pass


@client.command()
@commands.has_any_role('Moderator')  # This only works if the command is invoked in the server!
async def say(*, msg):
    await client.say(msg)


@client.command()
async def help():
    await client.say('I don\'t need any help from you right now, but thanks for asking.')


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

# Run the bot
client.run(TOKEN)
