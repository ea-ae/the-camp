import discord
import asyncio

from config import config


client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)


@client.event
async def on_message(message):
    print(message.content)
    print(message)
    await client.send_message(message.channel, 'Got it, ' + message.author + '!')


client.run(config['TOKEN'])
