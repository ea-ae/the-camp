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
