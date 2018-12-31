import discord
from discord.ext import commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime as dt


from config import *


class Events:
    """
    Events and scheduling.
    """

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def configurescheduler(self):
        try:
            if SCHEDULER_TYPE == 'redis':
                from apscheduler.jobstores.redis import RedisJobStore
                jobstores = {
                    'default': RedisJobStore(db=REDIS_DB_NUM)
                }
            elif SCHEDULER_TYPE == 'sqlalchemy':
                from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
                jobstores = {
                    'default': SQLAlchemyJobStore(url=f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')
                }
            else:
                from apscheduler.jobstores.memory import MemoryJobStore
                jobstores = {
                    'default': MemoryJobStore()
                }

            self.scheduler = AsyncIOScheduler(jobstores=jobstores, loop=self.client.loop)

            self.scheduler.start()
            self.scheduler.add_job(self.say_hi,
                                   'interval',
                                   seconds=5,
                                   args=[self], id='say_hi', replace_existing=True)
            self.scheduler.print_jobs()
        except Exception as e:
            import traceback
            traceback.print_exc()

    # Using staticmethods because of an issue with pickle (PicklingError: Can't pickle: it's not the same object as x)
    # If anyone knows how to fix it, be sure to tell me

    @staticmethod
    async def say_hi(self):
        await self.client.send_message(self.client.channels['say-hi'], 'Hi.')
        self.scheduler.add_job(self.late_hi,
                               'date',
                               run_date=(dt.datetime.now() + dt.timedelta(minutes=1)),
                               args=[self])
        self.scheduler.print_jobs()

    @staticmethod
    async def late_hi(self):
        await self.client.send_message(self.client.channels['say-hi'], 'Hi again!')


def setup(client):
    client.add_cog(Events(client))
