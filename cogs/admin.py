import discord
from discord.ext import commands

from .utils import get_user_roles, set_user_resources, update_camp_status


class Admin:
    """
    Commands for managing the bot.
    """

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True, aliases=['sd'])
    async def shutdown(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        print('Server stopped by command.')
        raise KeyboardInterrupt

    @commands.command(pass_context=True)
    async def reload(self, ctx, extension):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
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
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        try:
            self.client.load_extension(f'cogs.{extension}')
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension "{extension}":\n{type(e).__name__}\n{e}')

    @commands.command(pass_context=True)
    async def unload(self, ctx, extension):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        try:
            self.client.unload_extension(f'cogs.{extension}')
            print(f'Unloaded extension: {extension}')
        except Exception as e:
            print(f'Failed to unload extension "{extension}":\n{type(e).__name__}\n{e}')

    @commands.command(pass_context=True)
    async def say(self, ctx, *, msg):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return
        await self.client.say(msg)

    @commands.command(pass_context=True, aliases=['fillenergy'])
    async def instarest(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' in user_roles:
            await set_user_resources(self.client.db, ctx.message.author, {'energy': (12, False)})

    @commands.command(pass_context=True)
    async def updatecampstatus(self, ctx, reset_data='noreset'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' not in user_roles:
            return

        print('Updating camp status...')
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Developer' in user_roles:
            if reset_data == 'reset':
                await update_camp_status(self.client, True)
            else:
                await update_camp_status(self.client)


def setup(client):
    client.add_cog(Admin(client))
