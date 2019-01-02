import discord
from discord.ext import commands

import asyncio
import asyncpg

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import *


description = 'The Camp is a game about surviving together in a post-apocalypse world as long as possible.'
command_prefix = '!'
extensions = ['utils', 'core', 'admin', 'events', 'player', 'actions']


class CampBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(description=kwargs.pop('description'), command_prefix=kwargs.pop('command_prefix'))
        self.db = kwargs.pop('db')
        self.loop = kwargs.pop('loop')
        self.server = None
        self.channels = {}

    @property
    def utils(self):
        return self.get_cog('Utils')


def load_extensions(client):
    for extension in extensions:
        try:
            client.load_extension(f'cogs.{extension}')
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension "{extension}": {type(e).__name__}\n{e}')


async def run_event(event_name, *args):
    events = client.get_cog('Events')
    event = getattr(events, event_name)
    await event(*args)


# Run the bot
if __name__ == '__main__':
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

    client = CampBot(db=db, loop=loop, description=description, command_prefix=command_prefix)
    client.remove_command('help')
    load_extensions(client)

    if JOBSTORE == 'redis':
        from apscheduler.jobstores.redis import RedisJobStore
        jobstores = {
            'persistent': RedisJobStore(db=5)
        }
    elif JOBSTORE == 'sqlalchemy':
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
        jobstores = {
            'persistent': SQLAlchemyJobStore(url=f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')
        }
    else:
        print('WARNING: Unknown jobstore specified!')
        jobstores = {}

    client.scheduler = AsyncIOScheduler(jobstores=jobstores, loop=client.loop)

    client.scheduler.add_job(run_event,
                             'interval',
                             seconds=30,
                             args=['update_camp_status'],
                             id='update_camp_status',
                             replace_existing=True)

    client.scheduler.add_job(run_event,
                             'cron',
                             hour='0,6,12,18',
                             args=['random_camp_event'],
                             id='random_camp_event',
                             jobstore='persistent',
                             replace_existing=True)

    try:
        print('Logging in...')
        loop.run_until_complete(client.login(TOKEN))
        print('Connecting...')
        loop.run_until_complete(client.connect())
    except KeyboardInterrupt:
        print('KeyboardInterrupt!')
    finally:
        print('Shutting down scheduler...')
        client.scheduler.shutdown()
        print('Closing database...')
        loop.run_until_complete(db.close())
        print('Logging out...')
        loop.run_until_complete(client.logout())
        loop.close()
        print('Logged out!')
