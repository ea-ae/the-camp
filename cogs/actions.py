import discord
from discord.ext import commands

from .utils import get_user_roles, set_resources, update_camp_status


class Player:
    """
    Player-related commands.
    """

    def __init__(self, client):
        self.client = client

    @commands.group(pass_context=True)
    async def farm(self, ctx, amount='1'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if not any([role in user_roles for role in ('Alive', 'Dead')]):
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

    @commands.group(pass_context=True)
    async def mine(self, ctx, amount='1'):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if not any([role in user_roles for role in ('Alive', 'Dead')]):
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
        else:
            amount = int(amount)
            # The amount of materials mined will depend on character upgrades later on
            camp_mtr = amount
            personal_mtr = amount

            result = await set_resources(self.client.db,
                                         ctx.message.author,
                                         {'materials': personal_mtr, 'energy': -amount},
                                         {'materials': camp_mtr})

            if result is True:
                await self.client.say(
                    f'You earned **{camp_mtr}** material{"s" if camp_mtr > 1 else ""} for the camp '
                    f'and **{personal_mtr}** material{"s" if personal_mtr > 1 else ""} for yourself.')
                await update_camp_status(self.client)  # TODO: Do this task only once per min, not on every change!
            else:
                await self.client.say(result)


def setup(client):
    client.add_cog(Player(client))
