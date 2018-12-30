import discord
from discord.ext import commands
import random

from .utils import get_user_roles, set_resources, update_camp_status


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
        else:
            amount = int(amount)
            # The amount of food farmed will depend on character upgrades later on
            camp_food = amount
            personal_food = amount

            result = await set_resources(self.client.db,
                                         ctx.message.author,
                                         {'food': personal_food, 'energy': -amount},
                                         {'food': camp_food})

            if result is True:
                await self.client.say(
                    f'You earned **{camp_food}** food ration{"s" if camp_food > 1 else ""} for the camp '
                    f'and **{personal_food}** food ration{"s" if personal_food > 1 else ""} for yourself.')
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
        else:
            amount = int(amount)

            mats = random.randrange(0, amount + 1)
            fuel = (amount - mats) * 10

            result = await set_resources(self.client.db,
                                         ctx.message.author,
                                         {'materials': mats, 'fuel': fuel, 'energy': -amount},
                                         {'materials': mats, 'fuel': fuel})

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
        else:
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
                                          f'You were given **{amount}** scrap as the payment.')
                await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!
            else:
                if 'scrap' in result:  # The camp doesn't have enough scrap to pay for guarding
                    await self.client.say('The camp doesn\'t have enough scrap to pay for guarding.\n'
                                          'If you would like to work for free, type `!guard <amount> free`.')
                else:
                    await self.client.say(result)


def setup(client):
    client.add_cog(Player(client))
