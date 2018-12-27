import discord
import asyncio
import prettytable

from config import TOKEN


# Settings
SERVER_ID = '527261834852696064'

client = discord.Client()

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
async def on_message(message):
    asyncio.ensure_future(generate_status_message())  # Temporary

    if message.content.startswith('!'):
        parts = message.content[1:].split()

        user_roles = [role.name for role in server.get_member(message.author.id).roles]
        authorized = any([role in user_roles for role in ('Survivor', 'Veteran', 'Professional')])
        if parts[0] == 'say':
            if 'Moderator' in user_roles:
                await client.send_message(message.channel, ' '.join(parts[1:]))
        elif parts[0] == 'join' and len(parts) == 1:
            if authorized:
                await client.send_message(message.channel, 'You have already joined the camp!')
            else:
                await client.send_message(message.channel, 'You have joined the camp!')


@client.event
async def on_member_join(member):
    msg = ("""Welcome to **The Camp**, {0}!
All commands related to the game are sent in private messages.
To join the camp, simply type `!join`.""").format(member.mention)
    await client.send_message(member, msg)


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

client.run(TOKEN)
