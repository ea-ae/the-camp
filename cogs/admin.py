import discord
from discord.ext import commands

from .utils import get_user_roles


class Admin:
    """
    Commands for managing the bot.
    """

    def __init__(self, client):
        self.client = client

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
            print(f'Unoaded extension: {extension}')
        except Exception as e:
            print(f'Failed to unload extension "{extension}":\n{type(e).__name__}\n{e}')


def setup(client):
    client.add_cog(Admin(client))
