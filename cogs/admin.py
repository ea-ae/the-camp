import discord
from discord.ext import commands

from .events import Event


class Admin:
    """
    Commands for managing the bot.
    """

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True, aliases=['sd'])
    async def shutdown(self, ctx):
        """Shuts down the bot."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        print('Server stopped by command.')
        raise KeyboardInterrupt

    @commands.command(pass_context=True)
    async def reload(self, ctx, extension):
        """Reloads an extension."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        try:
            self.client.unload_extension(f'cogs.{extension}')
            self.client.load_extension(f'cogs.{extension}')
            print(f'Reloaded extension: {extension}')
        except Exception as e:
            print(f'Failed to reload extension "{extension}":\n{type(e).__name__}\n{e}')

    @commands.command(pass_context=True)
    async def load(self, ctx, extension):
        """Loads an extension."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        try:
            self.client.load_extension(f'cogs.{extension}')
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension "{extension}":\n{type(e).__name__}\n{e}')

    @commands.command(pass_context=True)
    async def unload(self, ctx, extension):
        """Unloads an extension."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        try:
            self.client.unload_extension(f'cogs.{extension}')
            print(f'Unloaded extension: {extension}')
        except Exception as e:
            print(f'Failed to unload extension "{extension}":\n{type(e).__name__}\n{e}')

    @commands.command(pass_context=True)
    async def say(self, ctx, *, msg):
        """Echoes a message."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return
        await self.client.say(msg)

    @commands.command(pass_context=True)
    async def setdata(self, ctx, data_name, data_value, user_id=None):
        """Sets a column to a given value in the players table."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return
        
        if user_id is None:
            user = ctx.message.author
        else:
            print(user_id)
            user = await self.client.get_user_info(user_id)

        data = dict()
        data[data_name] = (data_value, False)
        await self.client.utils.set_user_resources(self.client.db, user, data)

    @commands.command(pass_context=True, aliases=['ucs'])
    async def updatecampstatus(self, ctx, reset_data='noreset'):
        """Manually updates the camp's status."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        events = self.client.get_cog('Events')
        if reset_data == 'reset':
            await events.update_camp_status(True)
        else:
            await events.update_camp_status()

    @commands.command(pass_context=True)
    async def event(self, ctx, *, event_name=None):
        """Starts an event with a specific name."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        if event_name is None:
            event_names = ''
            for instance in Event.instances:
                event_names += f'{instance.title}\n'
            await self.client.say(event_names)
        else:
            for instance in Event.instances:
                if instance.title == event_name:
                    await instance.start_event()

    @commands.command(pass_context=True)
    async def debug(self, ctx, state):
        """Turns the debug mode on/off. Debug mode makes events pass instantly."""
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        if state in ('true', 'yes', 'y', 'on', '1'):
            print('Debug mode turned on!')
            Event.end_events_immediately = True
        elif state in ('false', 'no', 'n', 'off', '0'):
            print('Debug mode turned off!')
            Event.end_events_immediately = False

    @commands.command(pass_context=True)
    async def printjobs(self, ctx):
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        self.client.scheduler.print_jobs()


def setup(client):
    client.add_cog(Admin(client))
