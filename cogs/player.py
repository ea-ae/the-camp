import discord
from discord.ext import commands

from .utils import get_user_roles


class Player:
    """
    Player-related commands.
    """

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    async def status(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if any([role in user_roles for role in ('Alive', 'Dead')]):
            if 'Professional' in user_roles:
                rank = 'Professional'
                color = 0xf04c4c
            elif 'Veteran' in user_roles:
                rank = 'Veteran'
                color = 0xd1810d
            elif 'Survivor' in user_roles:
                rank = 'Survivor'
                color = 0xf0ca12
            else:
                rank = 'None'
                color = 0xffffff

            async with self.client.db.acquire() as conn:
                try:
                    query = '''SELECT xp, energy, status FROM players WHERE user_id = $1'''
                    result = await conn.fetchrow(query, ctx.message.author.id)
                except Exception as e:
                    await self.client.say('Something went wrong!')
                    print(e)
                else:
                    embed = discord.Embed(title=ctx.message.author.display_name, color=color)
                    embed.set_thumbnail(url=ctx.message.author.avatar_url)
                    embed.add_field(name='Rank', value=rank)
                    embed.add_field(name='XP', value=f'{result["xp"]} XP')
                    embed.add_field(name='Health', value=result['status'].capitalize())
                    embed.add_field(name='Energy', value=f'{result["energy"]}/10')
                    await self.client.say(embed=embed)

    @commands.command(pass_context=True, aliases=['house', 'inventory'])
    async def home(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if any([role in user_roles for role in ('Alive', 'Dead')]):
            if 'Professional' in user_roles:
                color = 0xf04c4c
            elif 'Veteran' in user_roles:
                color = 0xd1810d
            elif 'Survivor' in user_roles:
                color = 0xf0ca12
            else:
                color = 0xffffff

            # Temporary fake values
            food = 17
            fuel = 5
            medicine = 0
            materials = 36
            scrap = 107



            embed = discord.Embed(title='Your House',
                                  description='View possible house upgrades by typing `!build`.',
                                  color=color)
            embed.set_author(name=ctx.message.author.display_name)
            embed.add_field(name='Food', value=food)
            embed.add_field(name='Fuel', value=fuel)
            embed.add_field(name='Medicine', value=medicine)
            embed.add_field(name='Materials', value=materials)
            embed.add_field(name='Scrap', value=scrap)
            await self.client.say(embed=embed)


def setup(client):
    client.add_cog(Player(client))
