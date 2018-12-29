import discord
from discord.ext import commands
import traceback

from .utils import get_user_roles, set_user_resources, set_camp_resources, update_camp_status


class Player:
    """
    Player-related commands.
    """

    def __init__(self, client):
        self.client = client

    @commands.group(pass_context=True)
    async def farm(self, ctx, amount=1):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if not any([role in user_roles for role in ('Alive', 'Dead')]):
            return

        try:
            amount = int(amount)
        except ValueError:
            pass
        else:
            # The amount of food farmed will depend on character upgrades later on
            camp_food = amount
            personal_food = amount

            async with self.client.db.acquire() as conn:
                user_query = await set_user_resources(conn, ctx.message.author,
                                                      {'food': amount, 'energy': -amount}, False)
                print(user_query)

                if type(user_query) is str:  # Error
                    await self.client.say(user_query)
                    return

                camp_query = await set_camp_resources(conn, {'food': amount, 'medicine': 1, 'fuel': -10}, False)
                print(camp_query)

                if type(camp_query) is str:  # Error
                    await self.client.say(camp_query)
                    return

                tr = conn.transaction()
                await tr.start()

                try:
                    await conn.execute(user_query['query'], *user_query['args'])
                    await conn.execute(camp_query['query'])
                except Exception as e:
                    await tr.rollback()
                    print(e)
                    self.client.say('Something went wrong!')
                else:
                    await tr.commit()
                    await self.client.say(
                        f'You earned **{camp_food}** food ration{"s" if camp_food > 1 else ""} for the camp '
                        f'and **{personal_food}** food ration{"s" if personal_food > 1 else ""} for yourself.')

                    await update_camp_status(self.client)  # Temporary!

    @commands.group(pass_context=True)
    async def mine(self, ctx, amount=1):
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if not any([role in user_roles for role in ('Alive', 'Dead')]):
            return

        try:
            amount = int(amount)
        except ValueError:
            pass
        else:
            # The amount of food farmed will depend on character upgrades later on
            camp_mtr = amount
            personal_mtr = amount

            # TODO: Give the camp 1 food ration as well

            result = await set_user_resources(self.client.db, ctx.message.author, {'materials': amount,
                                                                                   'energy': -amount})
            if type(result) is str:  # Error
                await self.client.say(result)
            else:
                await self.client.say(
                    f'You earned **{camp_mtr}** material{"s" if camp_mtr > 1 else ""} for the camp '
                    f'and **{personal_mtr}** material{"s" if personal_mtr > 1 else ""} for yourself.')


def setup(client):
    client.add_cog(Player(client))
