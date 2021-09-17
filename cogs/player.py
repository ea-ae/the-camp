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
                return

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
        if result is False:
            await self.client.say('Something went wrong!')
            return

        description = ('View your available house upgrades with `!build`.\n'
                       'View your available crafting recipes with `!craft`.')

        max_energy = 12
        last_energy, energy = await update_user_energy(result['last_energy'], result['energy'], max_energy)

        embed = discord.Embed(title='Your House', description=description, color=color)
        embed.add_field(name='Food', value=result['food'])
        embed.add_field(name='Fuel', value=result['fuel'])
        embed.add_field(name='Medicine', value=result['medicine'])
        embed.add_field(name='Materials', value=result['materials'])
        embed.add_field(name='Scrap', value=result['scrap'])
        embed.add_field(name='Energy', value=f'{energy}/{max_energy}')

        await self.client.say(embed=embed)

    @commands.command(pass_context=True)
    async def build(self, ctx, upgrade=None):
        upgrade_list = {
            'safe': {
                'cost': [10, 20, 50],
                'description': 'Protect your belongings from thieves'
            },
            'heater': {
                'cost': [15, 30, 60],
                'description': 'Conserve fuel when heating your house'
            },
            'reinforcements': {
                'cost': [25, 50, 100],
                'description': 'Protect your house from any attacks'
            }
        }

        if upgrade is None:
            result = await get_user_columns(self.client.db, ctx.message.author, 'house_upgrades')
            if result is False:
                await self.client.say('Something went wrong!')
                return

            upgrades = json.loads(result['house_upgrades'])

            upgrade_msg = 'Build an house upgrade by typing `!build <upgrade_name>`.\n\n'
            for key, value in upgrade_list.items():
                if upgrades.get(key, 0) >= len(upgrade_list[key]['cost']):
                    cost = ''
                else:
                    cost = f' ({upgrade_list[key]["cost"][upgrades.get(key, 0)]} materials)'
                upgrade_msg += (
                    f'**{key.capitalize()} ({upgrades.get(key, 0)}/{len(upgrade_list[key]["cost"])})** - '
                    f'{upgrade_list[key]["description"]}{cost}.\n'
                )

            await self.client.say(upgrade_msg)
        elif upgrade.lower() in upgrade_list.keys(): 
            # Kind of inefficient (two SELECT queries for the same row are made), but whatever
            async with self.client.db.acquire() as conn:
                upgrade = upgrade.lower()
                result = await get_user_columns(conn, ctx.message.author, 'materials', 'house_upgrades')
                upgrades = json.loads(result['house_upgrades'])

                if upgrades.get(upgrade, 0) >= len(upgrade_list[upgrade]['cost']):
                    await self.client.say('This upgrade is already at maximum level.')
                else:
                    cost = upgrade_list[upgrade]['cost'][upgrades.get(upgrade, 0)]
                    upgrades[upgrade] = upgrades.get(upgrade, 0) + 1

                    result = await set_user_resources(
                        conn, ctx.message.author, 
                        {'materials': -cost, 'house_upgrades': (json.dumps(upgrades), False)}
                    )

                    if type(result) is str:
                        await self.client.say(result)
                    else:
                        await self.client.say(f'You have upgraded the **{upgrade}** to level '
                                            f'**{upgrades[upgrade]}** for **{cost}** materials.')
        else:
            await self.client.say('An upgrade with such a name doesn\'t exist! Type `!build` for a list of upgrades.')

def setup(client):
    client.add_cog(Player(client))
