import discord
from discord.ext import commands

from .utils import get_user_roles


class Ranks:
    """
    Manages ranks of players.
    """

    def __init__(self, client):
        self.client = client

    # TODO: Assign roles
    @commands.command(pass_context=True)
    async def join(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' in user_roles:
            await self.client.say('You have already joined the camp.')
        elif 'Dead' in user_roles:
            await self.client.say('You have already joined this game. Since you are dead, you have to wait till '
                                  'someone revives you or the next game starts.')
        else:
            await self.client.say('Welcome to **The Camp**! If it is your first time here, be sure to read the '
                                  'tutorial channel first. To see a list of available commands, type `!help`.')


def setup(client):
    client.add_cog(Ranks(client))
