import discord
from discord.ext import commands


class Camp:
    """
    Commands related to the camp.
    """

    def __init__(self, client):
        self.client = client


def setup(client):
    client.add_cog(Camp(client))
