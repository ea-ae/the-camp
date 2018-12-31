import discord
from discord.ext import commands
import json
import datetime

from .utils import (get_user_roles,
                    update_user_energy,
                    get_user_columns,
                    set_user_resources,
                    set_resources,
                    update_camp_status)


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

            result = await get_user_columns(self.client.db, ctx.message.author,
                                            'xp', 'status', 'energy', 'last_energy', 'food')
            if result is False:
                await self.client.say('Something went wrong!')
                return

            max_energy = 12  # Make max energy upgradable later on in the game (and keep it in the db)
            # We get the updated energy, but don't update it in the db, since it will be checked again anyway

            last_energy, energy = await update_user_energy(result['last_energy'],
                                                           result['energy'],
                                                           max_energy)

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
        if 'Alive' not in user_roles:
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
        last_energy, energy = await update_user_energy(result['last_energy'],
                                                       result['energy'],
                                                       max_energy)

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
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

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
                        {'materials': -cost, 'house_upgrades': (json.dumps(upgrades), False)},
                        user_result=result
                    )

                    if type(result) is str:  # Error
                        await self.client.say(result)
                    else:
                        await self.client.say(f'You have upgraded the **{upgrade}** to level '
                                              f'**{upgrades[upgrade]}** for **{cost}** materials.')
        else:
            await self.client.say('An upgrade with such a name doesn\'t exist! Type `!build` for a list of upgrades.')

    @commands.command(pass_context=True)
    async def craft(self, ctx, item=None, amount='1'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        items_list = {
            'heatarmor': {
                'name': 'Heat Armor',
                'desc': 'Heat armor warms you in extremely cold environments. It is required for scavenging',
                'cost': {
                    'scrap': 50
                }
            },
            'powercell': {
                'name': 'Power Cell',
                'desc': 'Heat armor requires power cells. One power cell is spent on every expedition',
                'cost': {
                    'scrap': 10,
                    'fuel': 50
                }
            },
            'farmwagon': {
                'name': 'Farm Wagon',
                'desc': 'Farm wagons let you haul larger amounts of food at once, earning you double the resources',
                'cost': {
                    'materials': 100
                }
            },
            'miningdrill': {
                'name': 'Mining Drill',
                'desc': 'Mining drills make mining double as fast, earning you double the resources',
                'cost': {
                    'scrap': 100,
                    'fuel': 100
                }
            }
        }

        if item is None:
            result = await get_user_columns(self.client.db, ctx.message.author, 'inventory')
            if result is False:
                await self.client.say('Something went wrong!')
                return

            inventory = json.loads(result['inventory'])

            inv_msg = ('Craft an item by typing `!craft <item_name> <amount>`. '
                       'Type the item\'s name without any spaces, e.g. `!craft heatarmor`.\n\n')
            for key, value in items_list.items():
                cost = []
                for resource_name, resource_amount in value["cost"].items():
                    cost.append(f'{resource_amount} {resource_name}')

                inv_msg += f'**{value["name"]} ({inventory.get(key, 0)}x)** - {value["desc"]} ({", ".join(cost)}).\n'

            await self.client.say(inv_msg)
        elif item.lower() in items_list.keys():
            if not amount.isdigit():
                await self.client.say('Invalid command!')
                return
            amount = int(amount)

            async with self.client.db.acquire() as conn:
                item = item.lower()

                resources_required = [resource[0] for resource in items_list[item]['cost'].items()]
                result = dict(await get_user_columns(conn, ctx.message.author, 'inventory', *resources_required))

                inventory = json.loads(result['inventory'])
                inventory[item] = inventory.get(item, 0) + amount

                cost = items_list[item]['cost']
                for key, value in cost.items():
                    cost[key] = value * -amount
                cost['inventory'] = (json.dumps(inventory), False)

                result = await set_user_resources(conn, ctx.message.author, cost, user_result=result)

                if type(result) is str:  # Error
                    await self.client.say(result)
                else:
                    await self.client.say(f'You have crafted the item{"s" if amount > 1 else ""} successfully!')
        else:
            await self.client.say('An item with such a name doesn\'t exist! Type `!craft` for a list of items.')

    @commands.command(pass_context=True)
    async def daily(self, ctx):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        async with self.client.db.acquire() as conn:
            result = dict(await get_user_columns(conn, ctx.message.author, 'last_daily', 'food'))
            if result['last_daily'] is None:
                result['last_daily'] = datetime.datetime.now() - datetime.timedelta(days=2)

            age = datetime.datetime.now() - result['last_daily']  # How much time has passed
            r = datetime.timedelta(days=1) - age  # Time remaining

            days, hours, minutes = r.days, r.seconds // 3600, r.seconds // 60 % 60

            if age < datetime.timedelta(days=1):
                await self.client.say(f'You have to wait {hours} hour{"s" if hours != 1 else ""} and '
                                      f'{minutes} minute{"s" if minutes != 1 else ""} for the next daily pack.')
                return

            result = await set_resources(conn, ctx.message.author,
                                         {'food': 24, 'last_daily': (str(datetime.datetime.now()), False)},
                                         {'food': -24}, user_result=result)

            if type(result) is str:  # Error
                await self.client.say(result)
            else:
                await self.client.say('You have redeemed your daily **24** food rations from the camp\'s warehouse.')
                await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!


def setup(client):
    client.add_cog(Player(client))
