import discord
import asyncio
import prettytable

from config import TOKEN


channels = {}
settings = {
    'SERVER_ID': '527261834852696064'
}

client = discord.Client()


@client.event
async def on_ready():
    server = client.get_server(settings['SERVER_ID'])
    for channel in server.channels:
        channels[channel.name] = client.get_channel(channel.id)

    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    await client.change_presence(game=discord.Game(name='Survived for 0 days'))


@client.event
async def on_message(message):
    if message.content.startswith('!'):
        parts = message.content[1:].split()
        if parts[0] == 'hello':
            await client.send_message(message.channel, 'world!')
        elif parts[0] == 'help':
            await client.send_message(message.channel, 'There is no help to be had.')

    # Temporary tables with fake data
    status_table = prettytable.PrettyTable(['Resource', 'Amount'])
    status_table.align = 'r'
    status_table.add_row(['Food', 725])
    status_table.add_row(['Fuel', 611])
    status_table.add_row(['Materials', 2509])
    status_table.add_row(['Medicine', 53])

    async for message in client.logs_from(channels['camp-status']):
        if message.author == client.user:
            status = '**Camp Resources**```' + str(status_table) + '```'
            await client.edit_message(message, status)
            break

client.run(TOKEN)
