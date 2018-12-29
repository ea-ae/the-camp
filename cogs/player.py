import discord
from discord.ext import commands

from .utils import get_user_roles, update_user_energy, get_user_columns, set_user_columns


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

            result = await get_user_columns(self.client.db, ctx.message.author, 'xp', 'energy', 'last_energy', 'status')
            if result is False:
                await self.client.say('Something went wrong!')
            else:
                max_energy = 12  # Make max energy upgradable later on in the game (and keep it in the db)
                # We get the updated energy, but don't update it in the db, since it will be checked again anyway

                last_energy, energy = await update_user_energy(result['last_energy'], result['energy'], max_energy)

                embed = discord.Embed(title=ctx.message.author.display_name, color=color)
                embed.set_thumbnail(url=ctx.message.author.avatar_url)
                embed.add_field(name='Rank', value=rank)
                embed.add_field(name='XP', value=f'{result["xp"]} XP')
                embed.add_field(name='Health', value=result['status'].capitalize())
                embed.add_field(name='Energy', value=f'{energy}/{max_energy}')

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

            # Test
            x = await set_user_columns(self.client.db, ctx.message.author, {'food': 1,
                                                                            'energy': -1,
                                                                            'scrap': 4,
                                                                            'fuel': (7, False)})
            print('Back to player.py........')
            print(x)
            result = await get_user_columns(self.client.db, ctx.message.author,
                                            'food', 'fuel', 'medicine', 'materials', 'scrap')

            embed = discord.Embed(title='Your House',
                                  description='Build house upgrades by typing `!build <upgrade_name>`.\n'
                                              '**Safe (0/3)** - Protect your belongings from thieves.\n'
                                              '**Heater (0/3)** - Conserve fuel when heating your house.\n'
                                              '**Reinforcements (0/3)** - Protect your house from any attacks.',
                                  color=color)
            embed.set_author(name=ctx.message.author.display_name)
            embed.add_field(name='Food', value=result['food'])
            embed.add_field(name='Fuel', value=result['fuel'])
            embed.add_field(name='Medicine', value=result['medicine'])
            embed.add_field(name='Materials', value=result['materials'])
            embed.add_field(name='Scrap', value=result['scrap'])
            await self.client.say(embed=embed)


def setup(client):
    client.add_cog(Player(client))
