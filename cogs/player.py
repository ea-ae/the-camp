import discord
from discord.ext import commands
import json

from .utils import get_user_roles, update_user_energy, get_user_columns, set_user_resources


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
        # TODO: Perhaps xp/energy should also be included in this command?
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if not any([role in user_roles for role in ('Alive', 'Dead')]):
            return

        if 'Professional' in user_roles:
            color = 0xf04c4c
        elif 'Veteran' in user_roles:
            color = 0xd1810d
        elif 'Survivor' in user_roles:
            color = 0xf0ca12
        else:
            color = 0xffffff

        result = await get_user_columns(
            self.client.db, ctx.message.author,
            'food', 'fuel', 'medicine', 'materials', 'scrap', 'energy', 'last_energy'
        )

        description = ('View your available house upgrades with `!build`.\n'
                       'View your available crafting recipes with `!craft`.')

        house_upgrades = ('**Safe (0/3)** - Protect your belongings from thieves.\n'
                          '**Heater (0/3)** - Conserve fuel when heating your house.\n'
                          '**Reinforcements (0/3)** - Protect your house from any attacks.\n')

        inventory = ('You don\'t have any items in your inventory.'
                     '')

        max_energy = 12
        last_energy, energy = await update_user_energy(result['last_energy'], result['energy'], max_energy)

        embed = discord.Embed(title='Your House', description=description, color=color)

        embed.add_field(name='House Upgrades', value=house_upgrades, inline=False)
        embed.add_field(name='Inventory', value=inventory, inline=False)

        embed.add_field(name='Food', value=result['food'])
        embed.add_field(name='Fuel', value=result['fuel'])
        embed.add_field(name='Medicine', value=result['medicine'])
        embed.add_field(name='Materials', value=result['materials'])
        embed.add_field(name='Scrap', value=result['scrap'])
        embed.add_field(name='Energy', value=f'{energy}/{max_energy}')

        await self.client.say(embed=embed)

    @commands.command(pass_context=True)
    async def build(self, ctx, upgrade=None):
        upgrade_costs = {
            'safe': [10, 20, 50],
            'heater': [15, 30, 60],
            'reinforcements': [25, 50, 100]
        }

        if upgrade is None:
            result = await get_user_columns(self.client.db, ctx.message.author, 'house_upgrades')
            upgrades = json.loads(result['house_upgrades'])

            await self.client.say(
                f'Build an house upgrade by typing `!build <upgrade_name>`.\n\n'
                f'**Safe ({upgrades.get("safe", 0)}/3)** - Protect your belongings from thieves '
                f'({upgrade_costs["safe"][upgrades.get("safe", 0)]} materials).\n'
                f'**Heater ({upgrades.get("heater", 0)}/3)** - Conserve fuel when heating your house '
                f'({upgrade_costs["heater"][upgrades.get("heater", 0)]} materials).\n'
                f'**Reinforcements ({upgrades.get("reinforcements", 0)}/3)** - Protect your house from attacks '
                f'({upgrade_costs["reinforcements"][upgrades.get("reinforcements", 0)]} materials).\n')
        elif upgrade.lower() in upgrade_costs.keys(): 
            # Kind of inefficient (two SELECT queries for the same row are made), but who cares anyway
            upgrade = upgrade.lower()
            result = await get_user_columns(self.client.db, ctx.message.author, 'house_upgrades')
            upgrades = json.loads(result['house_upgrades'])
            cost = upgrade_costs[upgrade][upgrades.get(upgrade, 0)]

            result = await set_user_resources(self.client.db, ctx.message.author, {'materials': -cost})

            if type(result) is str:
                await self.client.say(result)
            else:
                await self.client.say(f'You have upgraded the **{upgrade}** to level '
                                      f'**{upgrades.get(upgrade, 0) + 1}** for **{cost}** materials.')
        else:
            await self.client.say('No upgrades with such a name exist! Type `!build` for a list of upgrades.')

def setup(client):
    client.add_cog(Player(client))
