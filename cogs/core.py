import discord
from discord.ext import commands

from config import *


class Core:
    """
    Events, extension loading/unloading, and general-purpose commands.
    """

    def __init__(self, client):
        self.client = client

    async def on_ready(self):
        self.client.server = self.client.get_server(SERVER_ID)
        for channel in self.client.server.channels:
            self.client.channels[channel.name] = self.client.get_channel(channel.id)

        await self.client.change_presence(game=discord.Game(name='Survived for 0 days'))
        print(f'Ready!\nUser: {self.client.user.name} ({self.client.user.id})\n'
              f'Server: {self.client.server.name} ({self.client.server.id})')

    async def on_member_join(self, member):
        msg = (f'Welcome to **The Camp**, {member.mention}!\n'
               f'All commands related to the game are sent in private messages.\n'
               f'To join the camp, simply type `!join`.')
        await self.client.send_message(member, msg)

    async def on_command_error(self, error, ctx):
        if isinstance(error, commands.CommandNotFound):
            await self.client.send_message(ctx.message.channel, 'Unknown command. Type `!help` for a list of commands.')

    @commands.command()
    async def help(self, command=None):
        # await self.generate_status_message()  # TEMP
        # await self.client.say('I don\'t need any help from you right now, but thanks for asking.')
        if command is None:
            await self.client.say('**Basic Commands**\n'
                                  '`!help` - Show a list of commands.\n'
                                  '`!status` - View information about your character.\n'
                                  '`!home` - Check your inventory and home status.\n'
                                  '`!join` - Join a new game.\n'
                                  '\n*If you are confused about some game mechanic, read the docs channel.*')


def setup(client):
    client.add_cog(Core(client))
