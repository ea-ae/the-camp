import discord
from discord.ext import commands
import random
import json

from .utils import get_user_roles, get_user_columns, set_resources, update_camp_status


class Player:
    """
    Player-related commands.
    """

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    async def farm(self, ctx, amount='1'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        async with self.client.db.acquire() as conn:
            result = await get_user_columns(conn, ctx.message.author, 'inventory', 'food', 'energy', 'last_energy')

            food = amount

            inventory = json.loads(result['inventory'])
            if inventory.get('farmwagon', 0) > 0:
                food *= 2

            result = await set_resources(conn,
                                         ctx.message.author,
                                         {'food': food, 'energy': -amount},
                                         {'food': food},
                                         user_result=result)

        if result is True:
            await self.client.say(
                f'You earned **{food}** food ration{"s" if food > 1 else ""} for both yourself and the camp.')
            await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!
        else:
            await self.client.say(result)

    @commands.command(pass_context=True)
    async def mine(self, ctx, amount='1'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        async with self.client.db.acquire() as conn:
            result = await get_user_columns(conn, ctx.message.author,
                                            'inventory', 'materials', 'fuel', 'energy', 'last_energy', 'food')

            mats = random.randrange(0, amount + 1)
            fuel = (amount - mats) * 10

            inventory = json.loads(result['inventory'])
            if inventory.get('miningdrill', 0) > 0:
                mats *= 2
                fuel *= 2

            result = await set_resources(conn,
                                         ctx.message.author,
                                         {'materials': mats, 'fuel': fuel, 'energy': -amount},
                                         {'materials': mats, 'fuel': fuel},
                                         user_result=result)

        if result is True:
            await self.client.say(
                f'You earned **{mats}** material{"s" if mats > 1 or mats == 0 else ""} and '
                f'**{fuel}** fuel for both yourself and the camp.')
            await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!
        else:
            await self.client.say(result)

    @commands.command(pass_context=True)
    async def guard(self, ctx, amount='1', work_type=None):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        if work_type == 'free':
            result = await set_resources(self.client.db,
                                         ctx.message.author,
                                         {'energy': -amount},
                                         {'defense': amount})
        else:
            result = await set_resources(self.client.db,
                                         ctx.message.author,
                                         {'scrap': amount, 'energy': -amount},
                                         {'scrap': -amount, 'defense': amount})

        if result is True:
            if work_type == 'free':
                await self.client.say(f'The camp\'s defense increased by **{amount}**. '
                                      f'You were working for free and earned no scrap.')
            else:
                await self.client.say(f'The camp\'s defense increased by **{amount}**. '
                                      f'You were given **{amount}** scrap as payment.')
            await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!
        else:
            if 'scrap' in result:  # The camp doesn't have enough scrap to pay for guarding
                await self.client.say('The camp doesn\'t have enough scrap to pay for guarding.\n'
                                      'If you would like to work for free, type `!guard <amount> free`.')
            else:
                await self.client.say(result)


def setup(client):
    client.add_cog(Player(client))
