import discord
import asyncio
import prettytable

from config import TOKEN


# Settings
SERVER_ID = '527261834852696064'

client = discord.Client()
channels = {}


@client.event
async def on_ready():
    server = client.get_server(SERVER_ID)
    for channel in server.channels:
        channels[channel.name] = client.get_channel(channel.id)

    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    await client.change_presence(game=discord.Game(name='Survived for 0 days'))


@client.event
async def on_message(message):
    asyncio.ensure_future(generate_status_message())
    if message.content.startswith('!'):
        parts = message.content[1:].split()
        if parts[0] == 'say':
            if 'Moderator' in [role.name for role in message.author.roles]:
                await client.send_message(message.channel, ' '.join(parts[1:]))


async def generate_status_message():
    # Temporary fake data
    food = 725
    fuel = 205
    medicine = 53
    materials = 2509
    scrap = 9487

    days = 0
    temperature = -32
    defense = 5423

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
            status = '**Camp Status**```' + str(status_table) + '```**Warehouse**```' + str(warehouse_table) + '```'
            await client.edit_message(message, status)
            break

client.run(TOKEN)
